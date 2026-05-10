# tests/test_lists.py
import pytest
from sqlalchemy import select
from app.models.list import ItemList, ListItem


class TestListsEndpoints:
    """Тесты для эндпоинтов списков."""
    
    @pytest.mark.asyncio
    async def test_create_list_success(self, client, auth_headers):
        """Тест успешного создания списка."""
        response = await client.post(
            "/api/v1/lists/",
            json={"name": "My Test List"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test List"
        assert "id" in data
        assert "user_id" in data
    
    @pytest.mark.asyncio
    async def test_create_list_without_auth(self, client):
        """Тест создания списка без авторизации."""
        response = await client.post(
            "/api/v1/lists/",
            json={"name": "My Test List"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_my_lists(self, client, auth_headers, test_user, db_session):
        """Тест получения списков пользователя."""
        for i in range(3):
            list_item = ItemList(name=f"List {i}", user_id=test_user.id)
            db_session.add(list_item)
        await db_session.commit()
        
        response = await client.get("/api/v1/lists/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("name" in item for item in data)
    
    @pytest.mark.asyncio
    async def test_get_lists_pagination(self, client, auth_headers, test_user, db_session):
        """Тест пагинации списков."""
        for i in range(25):
            list_item = ItemList(
                name=f"Paginated List {i:02d}",
                user_id=test_user.id
            )
            db_session.add(list_item)
        await db_session.commit()
        
        # Страница 1
        response = await client.get(
            "/api/v1/lists/?page=1&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Страница 2
        response = await client.get(
            "/api/v1/lists/?page=2&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Страница 3 (должно быть 5)
        response = await client.get(
            "/api/v1/lists/?page=3&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    @pytest.mark.asyncio
    async def test_get_lists_sorting(self, client, auth_headers, test_user, db_session):
        """Тест сортировки списков по названию."""
        names = ["Banana List", "Apple List", "Cherry List"]
        for name in names:
            list_item = ItemList(name=name, user_id=test_user.id)
            db_session.add(list_item)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/lists/?sort_by=name&order=asc",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Apple List"
        assert data[1]["name"] == "Banana List"
        assert data[2]["name"] == "Cherry List"
    
    @pytest.mark.asyncio
    async def test_get_lists_filter_by_date(self, client, auth_headers, test_user, db_session):
        """Тест фильтрации списков по дате создания."""
        from datetime import datetime, timedelta, timezone
        
        old_date = datetime.now(timezone.utc) - timedelta(days=2)
        old_list = ItemList(name="Old List", user_id=test_user.id, created_at=old_date)
        db_session.add(old_list)
        
        new_list = ItemList(name="New List", user_id=test_user.id)
        db_session.add(new_list)
        await db_session.commit()
        
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        response = await client.get(
            f"/api/v1/lists/?created_after={yesterday}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "New List"