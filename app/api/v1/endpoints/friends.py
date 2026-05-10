# app/api/v1/endpoints/friends.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.friend import (
    FriendRequestCreate, FriendRequestResponse, 
    FriendResponse
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.friend_service import FriendService
from app.api.v1.descriptions import FRIENDS_GET_DESCRIPTION

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/requests", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request_data: FriendRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отправить заявку в друзья."""
    service = FriendService(db)
    try:
        return await service.send_request(current_user.id, request_data.friend_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/requests/incoming", response_model=List[FriendRequestResponse])
async def get_incoming_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить входящие заявки в друзья."""
    service = FriendService(db)
    return await service.get_incoming_requests(current_user.id)


@router.get("/requests/outgoing", response_model=List[FriendRequestResponse])
async def get_outgoing_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить исходящие заявки в друзья."""
    service = FriendService(db)
    return await service.get_outgoing_requests(current_user.id)


@router.put("/requests/{request_id}/accept", response_model=FriendRequestResponse)
async def accept_friend_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Принять заявку в друзья."""
    service = FriendService(db)
    try:
        return await service.accept_request(request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not pending" in str(e) 
            else status.HTTP_403_FORBIDDEN if "Not authorized" in str(e)
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/requests/{request_id}/reject", response_model=FriendRequestResponse)
async def reject_friend_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отклонить заявку в друзья."""
    service = FriendService(db)
    try:
        return await service.reject_request(request_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not pending" in str(e) 
            else status.HTTP_403_FORBIDDEN if "Not authorized" in str(e)
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=List[FriendResponse], description=FRIENDS_GET_DESCRIPTION)
async def get_friends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список друзей."""
    service = FriendService(db)
    return await service.get_friends(current_user.id)


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить из друзей."""
    service = FriendService(db)
    try:
        await service.remove_friend(current_user.id, friend_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )