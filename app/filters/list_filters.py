# app/filters/list_filters.py
from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter
from app.models.list import ItemList


class ItemListFilter(Filter):
    """Фильтр для списков."""
    name__ilike: Optional[str] = None
    user_id: Optional[int] = None
    
    order_by: list[str] = ["-created_at"]
    
    class Constants(Filter.Constants):
        model = ItemList
        search_model_fields = ["name"]