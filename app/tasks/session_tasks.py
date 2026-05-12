import asyncio
from app.task_queue import broker
from app.core.database import AsyncSessionLocal
from app.services.session_service import SessionService


@broker.task
async def check_session_timers() -> None:
    """Проверка таймеров сессий."""
    async with AsyncSessionLocal() as db:
        service = SessionService(db)
        updated = await service.check_countdowns_and_transition()
        if updated:
            print(f"⏱️ Обновлены сессии: {updated}")


@broker.task
async def cleanup_inactive_sessions() -> None:
    """Очистка неактивных сессий."""
    async with AsyncSessionLocal() as db:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select
        from app.models.session import Session, SessionStatus
        
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        result = await db.execute(
            select(Session).where(
                Session.status == SessionStatus.EDITING,
                Session.started_at < two_hours_ago
            )
        )
        sessions = result.scalars().all()
        
        for s in sessions:
            s.status = SessionStatus.CLOSED
        
        await db.commit()
        print(f"🧹 Очищено сессий: {len(sessions)}")