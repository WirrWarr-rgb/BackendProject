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