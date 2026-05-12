from app.task_queue import broker
from app.services.email_service import EmailService


@broker.task
async def send_welcome_email_task(email: str, username: str) -> None:
    """Отправка приветственного письма."""
    service = EmailService()
    await service.send_welcome_email(email, username)
    print(f"📧 Welcome email sent to {email}")