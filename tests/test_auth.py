import pytest


class TestAuthEndpoints:
    """Тесты для эндпоинтов аутентификации."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Тест успешной регистрации с проверкой роли по умолчанию."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Декодируем токен и проверяем роль
        from jose import jwt
        from app.core.config import settings
        
        payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Роль по умолчанию должна быть "user"
        assert payload.get("role") == "user"
        assert payload.get("sub") == "newuser@example.com"
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user_data):
        """Тест регистрации с уже существующим email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "anothername",
                "email": test_user_data["email"],  # Уже занят
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user_data):
        """Тест регистрации с уже существующим username."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": test_user_data["username"],  # Уже занят
                "email": "different@example.com",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user_data):
        """Тест успешного входа по email."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        
        # Проверяем, что в токене есть роль
        from jose import jwt
        from app.core.config import settings
        
        payload = jwt.decode(
            data["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert "role" in payload
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user_data):
        """Тест входа с неправильным паролем."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_wrong_email(self, client):
        """Тест входа с несуществующим email."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "email": "nonexistent@example.com",
                "password": "anypassword"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client, auth_headers, test_user_data):
        """Тест получения профиля текущего пользователя."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == "user"  # Проверяем роль
    
    @pytest.mark.asyncio
    async def test_admin_can_see_all_users(self, client, admin_auth_headers):
        """Тест: админ видит всех пользователей."""
        response = await client.get(
            "/api/v1/users/admin/all",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_user_cannot_see_all_users(self, client, auth_headers):
        """Тест: обычный пользователь НЕ может видеть всех пользователей."""
        response = await client.get(
            "/api/v1/users/admin/all",
            headers=auth_headers
        )
        
        assert response.status_code == 403  # Forbidden