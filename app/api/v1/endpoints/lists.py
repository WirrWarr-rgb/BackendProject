# app/api/v1/endpoints/lists.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.list import (
    ListCreate, ListResponse, ListUpdate,
    ListItemCreate, ListItemUpdate, ListItemResponse,
    BulkOrderUpdate
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.list_service import ListService

router = APIRouter(prefix="/lists", tags=["lists"])

# ============= Эндпоинты для списков =============

@router.post("/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_data: ListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать новый список."""
    service = ListService(db)
    return await service.create_list(current_user.id, list_data.name)


@router.get("/", response_model=List[ListResponse])
async def get_my_lists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Получить списки. Админ видит все, пользователь — только свои."""
    service = ListService(db)
    
    # Админ видит все списки
    if current_user.role.value == "admin":
        # Добавим метод в ListService позже, пока так
        from sqlalchemy import select
        result = await db.execute(
            select(ItemList)
            .offset(skip)
            .limit(limit)
            .order_by(ItemList.created_at.desc())
        )
        return result.scalars().all()
    
    # Обычный пользователь видит только свои
    return await service.get_user_lists(current_user.id, skip, limit)


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список по ID."""
    service = ListService(db)
    try:
        return await service.get_list_by_id(list_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: int,
    list_data: ListUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить список."""
    service = ListService(db)
    try:
        return await service.update_list(list_id, current_user.id, list_data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить список (и все его пункты)."""
    service = ListService(db)
    try:
        await service.delete_list(list_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============= Эндпоинты для пунктов списка =============

@router.post("/{list_id}/items", response_model=ListItemResponse, status_code=status.HTTP_201_CREATED)
async def create_list_item(
    list_id: int,
    item_data: ListItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Добавить пункт в список."""
    service = ListService(db)
    try:
        return await service.add_item(
            list_id=list_id,
            user_id=current_user.id,
            name=item_data.name,
            description=item_data.description,
            image_url=item_data.image_url,
            order_index=item_data.order_index
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{list_id}/items", response_model=List[ListItemResponse])
async def get_list_items(
    list_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить все пункты списка, отсортированные по order_index."""
    service = ListService(db)
    try:
        return await service.get_list_items(list_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/items/{item_id}", response_model=ListItemResponse)
async def update_list_item(
    item_id: int,
    item_data: ListItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить пункт списка."""
    service = ListService(db)
    try:
        return await service.update_item(
            item_id=item_id,
            user_id=current_user.id,
            name=item_data.name,
            description=item_data.description,
            image_url=item_data.image_url,
            order_index=item_data.order_index
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить пункт списка."""
    service = ListService(db)
    try:
        await service.delete_item(item_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============= Дополнительные эндпоинты =============

@router.post("/items/bulk-order", response_model=List[ListItemResponse])
async def bulk_update_order(
    list_id: int,
    order_data: BulkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Массовое обновление порядка пунктов (drag-and-drop)."""
    service = ListService(db)
    try:
        return await service.bulk_update_order(list_id, current_user.id, order_data.items)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/search/", response_model=List[ListResponse])
async def search_lists(
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """Поиск списков по названию."""
    service = ListService(db)
    return await service.search_lists(current_user.id, q, limit)


@router.get("/items/search/", response_model=List[ListItemResponse])
async def search_list_items(
    list_id: int,
    q: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """Поиск пунктов в списке по названию."""
    service = ListService(db)
    try:
        return await service.search_list_items(list_id, current_user.id, q, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/stats/", response_model=dict)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить статистику по спискам пользователя."""
    service = ListService(db)
    return await service.get_stats(current_user.id)


@router.post("/{list_id}/copy", response_model=ListResponse)
async def copy_list(
    list_id: int,
    new_name: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Скопировать список (со всеми пунктами)."""
    service = ListService(db)
    try:
        return await service.copy_list(list_id, current_user.id, new_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "permissions" in str(e).lower() 
            else status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )