# app/tasks/ai_tasks.py
import asyncio
from celery import Celery
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.ai_list_service import AIListService

celery_app = Celery(
    "decido_ai_tasks",
    broker=f"redis://localhost:6379/0",
    backend=f"redis://localhost:6379/1"
)

@celery_app.task(name="send_welcome_email")
def send_welcome_email_task(email: str, username: str):
    """Отправка приветственного письма."""
    import asyncio
    from app.services.email_service import EmailService
    
    async def _send():
        service = EmailService()
        return await service.send_welcome_email(email, username)
    
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_send())
    finally:
        loop.close()


@celery_app.task(name="generate_list_ai", bind=True, max_retries=2)
def generate_list_task(self, task_id: int, user_id: int, prompt: str, items_count: int):
    """
    Задача для фоновой генерации списка через LLM.
    
    Args:
        task_id: ID задачи в БД
        user_id: ID пользователя
        prompt: текстовый запрос
        items_count: желаемое количество пунктов
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            service = AIListService(db)
            return await service.generate_and_save_list(
                task_id=task_id,
                user_id=user_id,
                prompt=prompt,
                items_count=items_count
            )
    
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    except Exception as e:
        # Отмечаем задачу как Failed в БД
        async def _mark_failed():
            async with AsyncSessionLocal() as db:
                service = AIListService(db)
                await service.mark_failed(task_id, str(e))
        
        loop.run_until_complete(_mark_failed())
        raise
    finally:
        loop.close()
@celery_app.task(name="send_welcome_email")
def send_welcome_email_task(email: str, username: str):
    """Отправка приветственного письма."""
    import asyncio
    from app.services.email_service import EmailService
    
    async def _send():
        service = EmailService()
        return await service.send_welcome_email(email, username)
    
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_send())
    finally:
        loop.close()
