# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password, create_access_token


class AuthService:
    """Сервис аутентификации и регистрации"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register(
        self, 
        username: str, 
        email: str, 
        password: str,
        role: UserRole = UserRole.USER  # <-- ДОБАВЛЯЕМ параметр роли
    ) -> dict:
        """
        Регистрация нового пользователя.
        Только админ может создать другого админа.
        """
        # Проверяем, существует ли пользователь с таким email
        existing_email = await self.db.execute(
            select(User).where(User.email == email)
        )
        if existing_email.scalar_one_or_none():
            raise ValueError("User with this email already exists")
        
        # Проверяем, существует ли пользователь с таким username
        existing_username = await self.db.execute(
            select(User).where(User.username == username)
        )
        if existing_username.scalar_one_or_none():
            raise ValueError("Username already taken")
        
        # Создаем пользователя
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role  # <-- УСТАНАВЛИВАЕМ роль
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # Создаем токен с ролью
        access_token = create_access_token(
            data={
                "sub": new_user.email,
                "role": new_user.role.value  # <-- ДОБАВЛЯЕМ роль в токен
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    async def login(self, email: str, password: str) -> dict:
        """
        Вход пользователя по email и паролю.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect email or password")
        
        # Создаем токен с ролью
        access_token = create_access_token(
            data={
                "sub": user.email,
                "role": user.role.value  # <-- ДОБАВЛЯЕМ роль в токен
            }
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    async def get_user_by_email(self, email: str) -> User | None:
        """Получить пользователя по email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()