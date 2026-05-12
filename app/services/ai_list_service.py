import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.models.generated_list import GeneratedListTask, TaskStatus
from app.models.list import ItemList, ListItem
from app.models.user import User


# ============ Pydantic схема для Structured Output от LLM ============

class LLMListResponse(BaseModel):
    """
    Схема ответа от LLM.
    Список с названием и пунктами.
    """
    list_name: str = Field(description="Название списка")
    items: list[str] = Field(description="Пункты списка (названия)")
    description: Optional[str] = Field(None, description="Краткое описание списка")


class AIListService:
    """
    Сервис для AI-генерации списков через OpenRouter API.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, user_id: int, prompt: str, items_count: int) -> GeneratedListTask:
        """Создаёт задачу на генерацию."""
        task = GeneratedListTask(
            user_id=user_id,
            prompt=prompt,
            status=TaskStatus.PENDING
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_task(self, task_id: int, user_id: int) -> GeneratedListTask:
        """Получает задачу по ID."""
        result = await self.db.execute(
            select(GeneratedListTask).where(
                GeneratedListTask.id == task_id,
                GeneratedListTask.user_id == user_id
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        return task
    
    async def mark_processing(self, task_id: int) -> None:
        """Отмечает задачу как выполняющуюся."""
        task = await self.db.get(GeneratedListTask, task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(timezone.utc)
            await self.db.commit()
    
    async def mark_completed(self, task_id: int, list_id: int) -> None:
        """Отмечает задачу как завершённую."""
        task = await self.db.get(GeneratedListTask, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.list_id = list_id
            task.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
    
    async def mark_failed(self, task_id: int, error: str) -> None:
        """Отмечает задачу как проваленную."""
        task = await self.db.get(GeneratedListTask, task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error[:1000]
            await self.db.commit()
    
    async def generate_and_save_list(
        self,
        task_id: int,
        user_id: int,
        prompt: str,
        items_count: int
    ) -> int:
        """
        Основной метод: вызывает LLM, создаёт список с пунктами.
        Возвращает ID созданного списка.
        """
        await self.mark_processing(task_id)
        
        try:
            # 1. Вызов LLM
            llm_data = await self._call_llm(prompt, items_count)
            
            # 2. Создаём список
            new_list = ItemList(
                name=llm_data.list_name,
                user_id=user_id
            )
            self.db.add(new_list)
            await self.db.flush()
            
            # 3. Добавляем пункты
            for idx, item_name in enumerate(llm_data.items):
                list_item = ListItem(
                    list_id=new_list.id,
                    name=item_name,
                    description=llm_data.description if idx == 0 else None,
                    order_index=idx
                )
                self.db.add(list_item)
            
            await self.db.commit()
            await self.db.refresh(new_list)
            
            # 4. Отмечаем задачу как завершённую
            await self.mark_completed(task_id, new_list.id)
            
            print(f"🎉 Список '{new_list.name}' создан! ID: {new_list.id}, пунктов: {len(llm_data.items)}")
            return new_list.id
            
        except Exception as e:
            await self.db.rollback()
            await self.mark_failed(task_id, str(e))
            print(f"❌ Ошибка генерации списка: {e}")
            raise
    
    async def _call_llm(self, prompt: str, items_count: int) -> LLMListResponse:
        """
        Вызов LLM через OpenRouter API.
        """
        from openai import AsyncOpenAI
        from app.core.config import settings
        
        # Получаем API ключ (добавим в Settings)
        api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        
        system_prompt = f"""Ты - помощник для создания списков.
Сгенерируй список из {items_count} пунктов по запросу пользователя.
Верни ТОЛЬКО валидный JSON, соответствующий схеме.
Не добавляй пояснений вне JSON.
Для каждого пункта дай только название (без нумерации).
Название списка должно быть на русском языке."""

        # Формируем JSON схему для Structured Output
        schema = LLMListResponse.model_json_schema()
        
        response = await client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Запрос: {prompt}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "list_generation",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        result = LLMListResponse.model_validate(data)
        
        print(f"✅ LLM вернул список: '{result.list_name}' с {len(result.items)} пунктами")
        return result