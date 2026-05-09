"""add_user_role

Revision ID: 9620b5d8e2e0
Revises: 309f9e5553a0
Create Date: 2026-05-09 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9620b5d8e2e0'
down_revision: Union[str, None] = '309f9e5553a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём ENUM тип вручную
    userrole_enum = sa.Enum('ADMIN', 'USER', 'GUEST', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)
    
    # Добавляем колонку с временным значением по умолчанию
    op.add_column('users', sa.Column('role', userrole_enum, nullable=True))
    
    # Устанавливаем значение по умолчанию для существующих пользователей
    op.execute("UPDATE users SET role = 'USER' WHERE role IS NULL")
    
    # Делаем колонку NOT NULL
    op.alter_column('users', 'role', nullable=False)


def downgrade() -> None:
    # Удаляем колонку
    op.drop_column('users', 'role')
    
    # Удаляем ENUM тип
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)