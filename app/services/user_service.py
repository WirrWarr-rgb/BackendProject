# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.models.user import User
from app.schemas.user import UserUpdate

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Получить пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        return user
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Обновить профиль пользователя.
        Проверяет уникальность username и email.
        """
        user = await self.get_user_by_id(user_id)
        
        # Проверяем и обновляем username
        if user_data.username is not None:
            existing = await self.db.execute(
                select(User).where(User.username == user_data.username)
            )
            existing_user = existing.scalar_one_or_none()
            if existing_user and existing_user.id != user_id:
                raise ValueError("Username already taken")
            user.username = user_data.username
        
        # Проверяем и обновляем email
        if user_data.email is not None:
            existing = await self.db.execute(
                select(User).where(User.email == user_data.email)
            )
            existing_user = existing.scalar_one_or_none()
            if existing_user and existing_user.id != user_id:
                raise ValueError("Email already registered")
            user.email = user_data.email
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def search_users(self, query: str, exclude_user_id: int, limit: int = 20) -> List[User]:
        """Поиск пользователей по username (исключая указанного)"""
        result = await self.db.execute(
            select(User)
            .where(User.username.ilike(f"%{query}%"))
            .where(User.id != exclude_user_id)
            .limit(limit)
        )
        return result.scalars().all()