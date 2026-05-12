# app/tasks/run_timers.py
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.session_service import SessionService


async def run_timers():
    """Бесконечный цикл проверки таймеров."""
    print("⏱️ Запуск проверки таймеров сессий...")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = SessionService(db)
                updated = await service.check_countdowns_and_transition()
                if updated:
                    print(f"🔄 Обновлены сессии: {updated}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        await asyncio.sleep(5)  # Проверка каждые 5 секунд


if __name__ == "__main__":
    asyncio.run(run_timers())