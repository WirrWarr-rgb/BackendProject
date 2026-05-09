# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRoleEnum(str, Enum):
    """Роли пользователей для API"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRoleEnum = UserRoleEnum.USER  # По умолчанию USER, админ может указать другую


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[UserRoleEnum] = None  # Только админ может менять роль


class UserResponse(UserBase):
    id: int
    role: UserRoleEnum  # <-- ДОБАВЛЯЕМ роль в ответ
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: str | None = None
    role: UserRoleEnum | None = None  # <-- ДОБАВЛЯЕМ роль в токен