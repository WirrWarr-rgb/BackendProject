# app/schemas/list.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import datetime


# ============= Базовые схемы =============

class ListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ListCreate(ListBase):
    pass


class ListUpdate(BaseModel):
    """Схема для обновления списка"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ListResponse(ListBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============= Пункты списка =============

class ListItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    order_index: int = 0


class ListItemCreate(ListItemBase):
    pass


class ListItemUpdate(BaseModel):
    """Схема для обновления пункта списка"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    order_index: Optional[int] = None


class ListItemResponse(ListItemBase):
    id: int
    list_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============= Дополнительные схемы =============

class BulkOrderUpdate(BaseModel):
    """Схема для массового обновления порядка пунктов"""
    items: list[dict]  # [{"id": 1, "order_index": 0}, {"id": 2, "order_index": 1}]


# ============= Пагинация =============

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Обёртка для пагинированных ответов"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class ListPaginatedResponse(PaginatedResponse[ListResponse]):
    """Пагинированный ответ со списками"""
    pass

class ListGenerateRequest(BaseModel):
    """Схема запроса на генерацию списка через AI"""
    prompt: str = Field(
        ..., 
        min_length=10, 
        max_length=500,
        description="Описание желаемого списка (например: 'Хочу список из 10 хоррор фильмов')"
    )
    items_count: int = Field(
        10, 
        ge=3, 
        le=30, 
        description="Количество пунктов в списке (3-30)"
    )


class ListGenerateResponse(BaseModel):
    """Схема ответа на запрос генерации"""
    status: str = Field(description="Статус задачи")
    task_id: int = Field(description="ID задачи для отслеживания")
    message: str = Field(description="Сообщение пользователю")


class TaskStatusResponse(BaseModel):
    """Схема для проверки статуса задачи"""
    task_id: int
    status: str
    prompt: str
    list_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None