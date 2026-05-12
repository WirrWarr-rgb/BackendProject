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
from app.schemas.common import PaginationParams
from app.schemas.list import ListPaginatedResponse
from sqlalchemy import func, desc, asc
from datetime import datetime
from typing import Annotated
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from app.filters.list_filters import ItemListFilter
from app.services.ai_list_service import AIListService
from app.schemas.list import ListGenerateRequest, ListGenerateResponse, TaskStatusResponse
from app.tasks.ai_tasks import generate_list_task

from app.api.v1.descriptions import (
    LIST_GET_DESCRIPTION,
    LIST_ITEM_GET_DESCRIPTION,
    STATS_GET_DESCRIPTION
)

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


@router.get("/", response_model=Page[ListResponse])
async def get_my_lists(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    filter: Annotated[ItemListFilter, FilterDepends(ItemListFilter)],
):
    """Получить списки с пагинацией и фильтрацией."""
    service = ListService(db)
    
    user_id = None if current_user.role.value == "admin" else current_user.id
    
    return await service.get_user_lists_paginated(user_id=user_id, filter=filter)


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
        # Админ может редактировать любой список
        if current_user.role.value == "admin":
            return await service.update_list_admin(list_id, list_data.name)
        else:
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
        # Админ может удалить любой список
        if current_user.role.value == "admin":
            await service.delete_list_admin(list_id)
        else:
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


@router.get("/{list_id}/items", response_model=List[ListItemResponse], description=LIST_ITEM_GET_DESCRIPTION)
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


@router.get("/stats/", response_model=dict, description=STATS_GET_DESCRIPTION)
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

# ============= AI-генерация списка =============

@router.post("/generate", response_model=ListGenerateResponse,
    summary="Generate List With AI",
    description="""
    Запускает асинхронную генерацию списка через LLM (OpenRouter).
    
    Примеры запросов:
    - "Хочу список из 10 хоррор фильмов"
    - "Составь список книг по Python для начинающих"
    - "Подборка ресторанов Москвы с паназиатской кухней"
    
    Задача выполняется в фоне. Статус можно проверить через GET /lists/generate/{task_id}/status
    """)
async def generate_list(
    request: ListGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Запустить AI-генерацию списка.
    
    - **prompt**: текстовое описание желаемого списка (минимум 10 символов)
    - **items_count**: количество пунктов (от 3 до 30)
    """
    service = AIListService(db)
    
    try:
        # Создаём задачу в БД
        task = await service.create_task(
            user_id=current_user.id,
            prompt=request.prompt,
            items_count=request.items_count
        )
        
        await generate_list_task.kiq(task_id=task.id, user_id=current_user.id, prompt=request.prompt, items_count=request.items_count)
        
        return ListGenerateResponse(
            status="processing",
            task_id=task.id,
            message=f"Генерация списка началась. Проверьте статус: GET /lists/generate/{task.id}/status"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate/{task_id}/status", response_model=TaskStatusResponse,
    summary="Check List Generation Status")
async def check_generation_status(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Проверить статус задачи генерации списка.
    
    Возможные статусы:
    - **pending**: задача в очереди
    - **processing**: LLM генерирует список
    - **completed**: список создан (содержит list_id)
    - **failed**: ошибка генерации (содержит error_message)
    """
    service = AIListService(db)
    try:
        task = await service.get_task(task_id, current_user.id)
        return TaskStatusResponse(
            task_id=task.id,
            status=task.status.value,
            prompt=task.prompt,
            list_id=task.list_id,
            error_message=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))