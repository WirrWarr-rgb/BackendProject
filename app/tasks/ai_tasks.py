from app.task_queue import broker
from app.core.database import AsyncSessionLocal
from app.services.ai_list_service import AIListService


@broker.task
async def generate_list_task(task_id: int, user_id: int, prompt: str, items_count: int) -> None:
    """Генерация списка через LLM."""
    async with AsyncSessionLocal() as db:
        service = AIListService(db)
        await service.generate_and_save_list(
            task_id=task_id,
            user_id=user_id,
            prompt=prompt,
            items_count=items_count
        )