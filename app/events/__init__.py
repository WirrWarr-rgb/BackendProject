# app/events/__init__.py
"""
Модуль событийной модели.
Содержит обработчики событий SQLAlchemy.
"""
from app.events.handlers import register_all_events