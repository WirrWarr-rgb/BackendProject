# app/schemas/common.py
from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Общие параметры пагинации, сортировки и фильтрации"""
    page: int = Field(1, ge=1, description="Номер страницы (начиная с 1)")
    per_page: int = Field(20, ge=1, le=100, description="Количество элементов на странице")
    sort_by: Optional[str] = Field(None, description="Поле для сортировки")
    order: Optional[str] = Field("asc", description="Направление сортировки: asc или desc")
    search: Optional[str] = Field(None, description="Поисковый запрос")
    created_after: Optional[datetime] = Field(None, description="Созданы после этой даты")
    created_before: Optional[datetime] = Field(None, description="Созданы до этой даты")


class PaginatedResponse(BaseModel, Generic[T]):
    """Обёртка для пагинированных ответов"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool