# app/services/friend_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List
from app.models.user import User
from app.models.friend import Friend, FriendStatus

class FriendService:
    """Сервис для работы с друзьями и заявками"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def send_request(self, from_user_id: int, to_user_id: int) -> Friend:
        """Отправить заявку в друзья"""
        # Проверяем, что пользователь не отправляет заявку сам себе
        if to_user_id == from_user_id:
            raise ValueError("Cannot send friend request to yourself")
        
        # Проверяем, существует ли пользователь
        result = await self.db.execute(
            select(User).where(User.id == to_user_id)
        )
        friend = result.scalar_one_or_none()
        if not friend:
            raise ValueError("User not found")
        
        # Проверяем, нет ли уже заявки или дружбы
        existing_request = await self.db.execute(
            select(Friend).where(
                or_(
                    and_(Friend.user_id == from_user_id, Friend.friend_id == to_user_id),
                    and_(Friend.user_id == to_user_id, Friend.friend_id == from_user_id)
                )
            )
        )
        existing = existing_request.scalar_one_or_none()
        if existing:
            if existing.status == FriendStatus.PENDING:
                raise ValueError("Friend request already pending")
            elif existing.status == FriendStatus.ACCEPTED:
                raise ValueError("You are already friends")
        
        # Создаем заявку
        friend_request = Friend(
            user_id=from_user_id,
            friend_id=to_user_id,
            status=FriendStatus.PENDING
        )
        self.db.add(friend_request)
        await self.db.commit()
        await self.db.refresh(friend_request)
        return friend_request
    
    async def get_incoming_requests(self, user_id: int) -> List[Friend]:
        """Получить входящие заявки в друзья"""
        result = await self.db.execute(
            select(Friend)
            .where(Friend.friend_id == user_id)
            .where(Friend.status == FriendStatus.PENDING)
            .order_by(Friend.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_outgoing_requests(self, user_id: int) -> List[Friend]:
        """Получить исходящие заявки в друзья"""
        result = await self.db.execute(
            select(Friend)
            .where(Friend.user_id == user_id)
            .where(Friend.status == FriendStatus.PENDING)
            .order_by(Friend.created_at.desc())
        )
        return result.scalars().all()
    
    async def accept_request(self, request_id: int, current_user_id: int) -> Friend:
        """Принять заявку в друзья"""
        # Находим заявку
        result = await self.db.execute(
            select(Friend).where(Friend.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise ValueError("Friend request not found")
        
        # Проверяем, что заявка адресована текущему пользователю
        if request.friend_id != current_user_id:
            raise ValueError("Not authorized to accept this request")
        
        # Проверяем, что заявка в статусе pending
        if request.status != FriendStatus.PENDING:
            raise ValueError("Friend request is not pending")
        
        # Принимаем заявку
        request.status = FriendStatus.ACCEPTED
        await self.db.commit()
        await self.db.refresh(request)
        return request
    
    async def reject_request(self, request_id: int, current_user_id: int) -> Friend:
        """Отклонить заявку в друзья"""
        # Находим заявку
        result = await self.db.execute(
            select(Friend).where(Friend.id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            raise ValueError("Friend request not found")
        
        # Проверяем, что заявка адресована текущему пользователю
        if request.friend_id != current_user_id:
            raise ValueError("Not authorized to reject this request")
        
        # Проверяем, что заявка в статусе pending
        if request.status != FriendStatus.PENDING:
            raise ValueError("Friend request is not pending")
        
        # Отклоняем заявку
        request.status = FriendStatus.REJECTED
        await self.db.commit()
        await self.db.refresh(request)
        return request
    
    async def get_friends(self, user_id: int) -> List[User]:
        """Получить список друзей пользователя"""
        # Находим все принятые заявки, где пользователь - инициатор или получатель
        result = await self.db.execute(
            select(Friend)
            .where(
                or_(
                    and_(Friend.user_id == user_id, Friend.status == FriendStatus.ACCEPTED),
                    and_(Friend.friend_id == user_id, Friend.status == FriendStatus.ACCEPTED)
                )
            )
        )
        friendships = result.scalars().all()
        
        # Получаем данные друзей
        friends = []
        for f in friendships:
            friend_id = f.friend_id if f.user_id == user_id else f.user_id
            result = await self.db.execute(select(User).where(User.id == friend_id))
            friend = result.scalar_one()
            friends.append(friend)
        
        return friends
    
    async def remove_friend(self, user_id: int, friend_id: int) -> None:
        """Удалить из друзей"""
        # Находим дружбу
        result = await self.db.execute(
            select(Friend)
            .where(
                or_(
                    and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                    and_(Friend.friend_id == user_id, Friend.user_id == friend_id)
                )
            )
            .where(Friend.status == FriendStatus.ACCEPTED)
        )
        friendship = result.scalar_one_or_none()
        
        if not friendship:
            raise ValueError("Friendship not found")
        
        await self.db.delete(friendship)
        await self.db.commit()