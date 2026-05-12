from celery import Celery
from app.services.email_service import EmailService

celery_app = Celery("email_tasks", broker="redis://localhost:6379/0")


@celery_app.task(name="send_welcome_email")
def send_welcome_email_task(email: str, username: str):
    """Отправка приветственного письма (синхронная обёртка)."""
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