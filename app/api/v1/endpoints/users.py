# app/api/v1/endpoints/users.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserRoleEnum
from app.api.v1.endpoints.auth import get_current_user
from app.services.user_service import UserService
from app.core.permissions import require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Получить профиль текущего пользователя."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Обновить профиль текущего пользователя."""
    service = UserService(db)
    try:
        return await service.update_user(current_user.id, user_data, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/search/", response_model=list[UserResponse])
async def search_users(
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    """Поиск пользователей по username."""
    service = UserService(db)
    return await service.search_users(q, current_user.id, limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Получить пользователя по ID."""
    service = UserService(db)
    try:
        return await service.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============= АДМИНСКИЕ МЕТОДЫ =============

@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    new_role: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
):
    """
    Изменить роль пользователя (только для администратора).
    
    - **new_role**: admin, user, guest
    """
    service = UserService(db)
    try:
        update_data = UserUpdate(role=UserRoleEnum(new_role))
        return await service.update_user(user_id, update_data, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin/all", response_model=list[UserResponse])
async def get_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
):
    """Получить всех пользователей (только для администратора)."""
    result = await db.execute(select(User))
    return result.scalars().all()