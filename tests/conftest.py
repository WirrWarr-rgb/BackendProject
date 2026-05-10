# tests/conftest.py
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole

TEST_DATABASE_URL = settings.DATABASE_URL

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Очищает таблицы перед каждым тестом."""
    async with TestSessionLocal() as session:
        tables = [
            "session_results", "session_participants",
            "session_list_items", "session_lists",
            "sessions", "list_items", "lists",
            "friends", "users"
        ]
        for table in tables:
            try:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass
        await session.commit()
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP клиент с полным моком SMTP."""
    # Мокаем ВЕСЬ aiosmtplib.send на уровне модуля
    with patch('aiosmtplib.send', new_callable=AsyncMock, return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_admin_data():
    return {
        "username": "testadmin",
        "email": "admin_test@example.com",
        "password": "admin123456",
    }


@pytest_asyncio.fixture
async def test_user(db_session, test_user_data):
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session, test_admin_data):
    admin = User(
        username=test_admin_data["username"],
        email=test_admin_data["email"],
        hashed_password=get_password_hash(test_admin_data["password"]),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_token(client, test_user, test_user_data):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    data = response.json()
    return data.get("access_token")


@pytest_asyncio.fixture
async def admin_auth_token(client, test_admin, test_admin_data):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "email": test_admin_data["email"],
            "password": test_admin_data["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    data = response.json()
    return data.get("access_token")


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(admin_auth_token):
    return {"Authorization": f"Bearer {admin_auth_token}"}