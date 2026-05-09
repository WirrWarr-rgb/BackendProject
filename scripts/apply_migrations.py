# apply_migrations.py
import asyncio
from app.core.database import engine, Base
from app.models.user import User
from app.models.list import ItemList, ListItem
from app.models.friend import Friend
from app.models.session import (
    Session, SessionParticipant, SessionResult,
    SessionList, SessionListItem
)

async def apply():
    print("Создаю все таблицы...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Все таблицы успешно созданы!")

if __name__ == "__main__":
    asyncio.run(apply())