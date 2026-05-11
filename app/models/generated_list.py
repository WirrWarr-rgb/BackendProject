# app/models/generated_list.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    """Статусы задачи генерации списка"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedListTask(Base):
    """Задача на генерацию списка через LLM"""
    __tablename__ = "generated_list_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    prompt = Column(String(500), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    error_message = Column(String(1000), nullable=True)
    
    # Результат
    list_id = Column(Integer, ForeignKey("lists.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)