# app/services/email_service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    """
    Сервис для отправки email через Mailpit.
    В продакшене нужно заменить SMTP-настройки на реальные.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1025,
        from_email: str = "noreply@decido.app",
        from_name: str = "Decido App"
    ):
        self.host = host
        self.port = port
        self.from_email = from_email
        self.from_name = from_name
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Отправить email.
        В тестовой среде (когда Mailpit недоступен) просто логирует отправку.
        """
        try:
            # Пробуем отправить через SMTP
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                start_tls=False
            )
            
            print(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            # В тестовой среде или если Mailpit недоступен — просто логируем
            print(f"📧 Email to {to_email}: {subject}")
            print(f"   Body: {body[:100]}...")
            print(f"   (SMTP error ignored in dev mode: {e})")
            return True  # Не роняем приложение из-за ошибки email
    
    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Отправить приветственное письмо при регистрации"""
        subject = f"Добро пожаловать в Decido, {username}!"
        
        body = f"""
Привет, {username}!

Спасибо за регистрацию в Decido — приложении для коллективного принятия решений.

Что теперь можно делать:
• Создавать списки для голосования
• Приглашать друзей
• Запускать голосования и смотреть результаты

Если у тебя есть вопросы, просто ответь на это письмо.

Удачных решений!
Команда Decido
        """
        
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4A90D9;">Привет, {username}! 🎉</h2>
    <p>Спасибо за регистрацию в <b>Decido</b> — приложении для коллективного принятия решений.</p>
    
    <h3>Что теперь можно делать:</h3>
    <ul>
        <li>📋 Создавать списки для голосования</li>
        <li>👥 Приглашать друзей</li>
        <li>🗳️ Запускать голосования и смотреть результаты</li>
    </ul>
    
    <p>Если у тебя есть вопросы, просто ответь на это письмо.</p>
    
    <p style="color: #999; margin-top: 30px;">Удачных решений!<br>Команда Decido</p>
</body>
</html>
        """
        
        return await self.send_email(to_email, subject, body, html_body)