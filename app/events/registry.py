# app/events/registry.py
"""
Регистрация всех обработчиков событий при запуске приложения.
"""

def init_events():
    """Инициализация событийной модели."""
    from app.events.handlers import register_all_events
    register_all_events()
    print("🔔 Событийная модель активирована")