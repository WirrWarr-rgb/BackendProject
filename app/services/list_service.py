from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict
from app.models.list import ItemList, ListItem
from app.models.user import User
from typing import Optional
from sqlalchemy import func, desc, asc
from datetime import datetime
from fastapi_filter import FilterDepends
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page
from app.filters.list_filters import ItemListFilter


class ListService:
    """Сервис для работы со списками и пунктами"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =============== СПИСКИ ===============
    
    async def create_list(self, user_id: int, name: str) -> ItemList:
        """Создать новый список"""
        new_list = ItemList(
            name=name,
            user_id=user_id
        )
        self.db.add(new_list)
        await self.db.commit()
        await self.db.refresh(new_list)
        return new_list
    
    async def get_user_lists_paginated(
        self,
        user_id: Optional[int] = None,
        filter: "ItemListFilter" = None,
    ):
        """Получить списки с пагинацией через fastapi-pagination."""
        from app.models.list import ItemList
        from sqlalchemy import select
        
        query = select(ItemList)
        
        if user_id is not None:
            query = query.where(ItemList.user_id == user_id)
        
        if filter:
            query = filter.filter(query)
            query = filter.sort(query)
        
        return await paginate(self.db, query)
    
    async def get_list_by_id(self, list_id: int, user_id: int) -> ItemList:
        """Получить список по ID с проверкой прав"""
        result = await self.db.execute(
            select(ItemList).where(ItemList.id == list_id)
        )
        list_item = result.scalar_one_or_none()
        
        if not list_item:
            raise ValueError("List not found")
        
        if list_item.user_id != user_id:
            raise ValueError("Not enough permissions")
        
        return list_item
    
    async def update_list(self, list_id: int, user_id: int, name: Optional[str] = None) -> ItemList:
        """Обновить список"""
        list_item = await self.get_list_by_id(list_id, user_id)
        
        if name is not None:
            list_item.name = name
        
        await self.db.commit()
        await self.db.refresh(list_item)
        return list_item
    
    async def delete_list(self, list_id: int, user_id: int) -> None:
        """Удалить список (и все его пункты каскадно)"""
        list_item = await self.get_list_by_id(list_id, user_id)
        await self.db.delete(list_item)
        await self.db.commit()
    
    async def search_lists(
        self, 
        user_id: int, 
        query: str, 
        limit: int = 20
    ) -> List[ItemList]:
        """Поиск списков по названию"""
        result = await self.db.execute(
            select(ItemList)
            .where(ItemList.user_id == user_id)
            .where(ItemList.name.ilike(f"%{query}%"))
            .limit(limit)
            .order_by(ItemList.created_at.desc())
        )
        return result.scalars().all()
    
    async def copy_list(
        self, 
        list_id: int, 
        user_id: int, 
        new_name: Optional[str] = None
    ) -> ItemList:
        """Скопировать список со всеми пунктами"""
        original_list = await self.get_list_by_id(list_id, user_id)
        
        # Создаем копию списка
        copied_list = ItemList(
            name=new_name or f"{original_list.name} (copy)",
            user_id=user_id
        )
        self.db.add(copied_list)
        await self.db.flush()  # Получаем ID нового списка
        
        # Копируем все пункты
        items_result = await self.db.execute(
            select(ListItem).where(ListItem.list_id == list_id)
        )
        original_items = items_result.scalars().all()
        
        for item in original_items:
            new_item = ListItem(
                list_id=copied_list.id,
                name=item.name,
                description=item.description,
                image_url=item.image_url,
                order_index=item.order_index
            )
            self.db.add(new_item)
        
        await self.db.commit()
        await self.db.refresh(copied_list)
        return copied_list
    
    async def get_stats(self, user_id: int) -> Dict:
        """Получить статистику по спискам пользователя"""
        # Общее количество списков
        lists_count_result = await self.db.execute(
            select(ItemList).where(ItemList.user_id == user_id)
        )
        lists_count = len(lists_count_result.scalars().all())
        
        # Общее количество пунктов во всех списках
        items_count_result = await self.db.execute(
            select(ListItem)
            .join(ItemList)
            .where(ItemList.user_id == user_id)
        )
        items_count = len(items_count_result.scalars().all())
        
        # Список с наибольшим количеством пунктов
        top_list_result = await self.db.execute(
            select(ItemList)
            .where(ItemList.user_id == user_id)
            .order_by(ItemList.id)
        )
        
        # Считаем количество пунктов для каждого списка
        list_items_counts = {}
        for list_item in top_list_result.scalars().all():
            count_result = await self.db.execute(
                select(ListItem).where(ListItem.list_id == list_item.id)
            )
            list_items_counts[list_item.name] = len(count_result.scalars().all())
        
        top_list = max(list_items_counts.items(), key=lambda x: x[1]) if list_items_counts else ("None", 0)
        
        return {
            "total_lists": lists_count,
            "total_items": items_count,
            "list_with_most_items": {
                "name": top_list[0],
                "items_count": top_list[1]
            }
        }
    
    # =============== ПУНКТЫ СПИСКА ===============
    
    async def add_item(
        self,
        list_id: int,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        order_index: int = 0
    ) -> ListItem:
        """Добавить пункт в список"""
        # Проверяем, что список существует и принадлежит пользователю
        await self.get_list_by_id(list_id, user_id)
        
        # Если order_index не указан, ставим в конец
        if order_index == 0:
            max_order_result = await self.db.execute(
                select(ListItem.order_index)
                .where(ListItem.list_id == list_id)
                .order_by(ListItem.order_index.desc())
                .limit(1)
            )
            max_order = max_order_result.scalar_one_or_none()
            order_index = (max_order + 1) if max_order is not None else 0
        
        new_item = ListItem(
            list_id=list_id,
            name=name,
            description=description,
            image_url=image_url,
            order_index=order_index
        )
        
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)
        return new_item
    
    async def get_list_items(self, list_id: int, user_id: int) -> List[ListItem]:
        """Получить все пункты списка"""
        await self.get_list_by_id(list_id, user_id)
        
        result = await self.db.execute(
            select(ListItem)
            .where(ListItem.list_id == list_id)
            .order_by(ListItem.order_index)
        )
        return result.scalars().all()
    
    async def update_item(
        self,
        item_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        order_index: Optional[int] = None
    ) -> ListItem:
        """Обновить пункт списка"""
        # Находим пункт
        result = await self.db.execute(
            select(ListItem).where(ListItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise ValueError("Item not found")
        
        # Проверяем права через родительский список
        list_result = await self.db.execute(
            select(ItemList).where(ItemList.id == item.list_id)
        )
        list_item = list_result.scalar_one_or_none()
        
        if not list_item or list_item.user_id != user_id:
            raise ValueError("Not enough permissions")
        
        # Обновляем только переданные поля
        if name is not None:
            item.name = name
        if description is not None:
            item.description = description
        if image_url is not None:
            item.image_url = image_url
        if order_index is not None:
            item.order_index = order_index
        
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def delete_item(self, item_id: int, user_id: int) -> None:
        """Удалить пункт списка"""
        # Находим пункт
        result = await self.db.execute(
            select(ListItem).where(ListItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise ValueError("Item not found")
        
        # Проверяем права через родительский список
        list_result = await self.db.execute(
            select(ItemList).where(ItemList.id == item.list_id)
        )
        list_item = list_result.scalar_one_or_none()
        
        if not list_item or list_item.user_id != user_id:
            raise ValueError("Not enough permissions")
        
        await self.db.delete(item)
        await self.db.commit()
    
    async def bulk_update_order(
        self,
        list_id: int,
        user_id: int,
        items_order: List[dict]
    ) -> List[ListItem]:
        """Массовое обновление порядка пунктов"""
        await self.get_list_by_id(list_id, user_id)
        
        for item_update in items_order:
            await self.db.execute(
                update(ListItem)
                .where(ListItem.id == item_update["id"])
                .where(ListItem.list_id == list_id)
                .values(order_index=item_update["order_index"])
            )
        
        await self.db.commit()
        
        result = await self.db.execute(
            select(ListItem)
            .where(ListItem.list_id == list_id)
            .order_by(ListItem.order_index)
        )
        return result.scalars().all()
    
    async def search_list_items(
        self,
        list_id: int,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> List[ListItem]:
        """Поиск пунктов в списке по названию"""
        await self.get_list_by_id(list_id, user_id)
        
        result = await self.db.execute(
            select(ListItem)
            .where(ListItem.list_id == list_id)
            .where(ListItem.name.ilike(f"%{query}%"))
            .limit(limit)
            .order_by(ListItem.order_index)
        )
        return result.scalars().all()