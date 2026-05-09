# scripts/create_admin.py
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select


async def create_admin():
    """Создать первого администратора"""
    async with AsyncSessionLocal() as db:
        # Проверяем, есть ли уже админ
        result = await db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            print(f"Admin already exists: {admin.email}")
            return
        
        # Создаём админа
        hashed_password = get_password_hash("admin123456")
        admin_user = User(
            username="admin",
            email="admin@decido.app",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
        print("✅ Admin created: admin@decido.app / admin123456")


if __name__ == "__main__":
    asyncio.run(create_admin())