# app/events/handlers.py
"""
Обработчики событий SQLAlchemy.

События:
- user.registered — пользователь зарегистрирован
- session.status_changed — изменён статус сессии
- session.voting_completed — голосование завершено
- friend.request_sent — отправлена заявка в друзья
- friend.request_accepted — заявка принята
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.orm import Session as DBSession

from app.models.user import User
from app.models.session import Session, SessionStatus
from app.models.friend import Friend, FriendStatus


# ============================================================
# СОБЫТИЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================

@event.listens_for(User, 'after_insert')
def on_user_registered(mapper, connection, target: User):
    """
    Событие: пользователь зарегистрирован.
    
    Что происходит:
    1. Логирование в консоль
    2. Отправка приветственного письма (если запущено в event loop)
    """
    print(f"""
╔══════════════════════════════════════════╗
║ 🔔 СОБЫТИЕ: user.registered              ║
║    Пользователь: {target.username:<20} ║
║    Email: {target.email:<30} ║
║    Роль: {target.role.value:<30} ║
║    Время: {datetime.now(timezone.utc).isoformat():<30} ║
╚══════════════════════════════════════════╝
    """)
    
    # Отправка приветственного письма через Celery
    try:
        from app.tasks.email_tasks import send_welcome_email_task
        # Запускаем задачу асинхронно
        send_welcome_email_task.delay(target.email, target.username)
        print(f"   📧 Задача на отправку welcome email создана")
    except ImportError:
        print(f"   ⚠️ Celery не настроен, пропускаем отправку email")
    except Exception as e:
        print(f"   ❌ Ошибка при создании задачи: {e}")


# ============================================================
# СОБЫТИЯ СЕССИЙ
# ============================================================

@event.listens_for(Session.status, 'set', active_history=True)
def on_session_status_changed(
    target: Session, 
    value: SessionStatus, 
    oldvalue: SessionStatus, 
    initiator
):
    """
    Событие: статус сессии изменён.
    
    Отслеживаем ключевые переходы:
    - WAITING → EDITING (все приняли приглашение)
    - EDITING → VOTING (голосование началось)
    - VOTING → RESULTS (голосование завершено)
    - RESULTS → CLOSED (лобби закрыто)
    """
    # Игнорируем начальную установку (когда oldvalue — специальный объект)
    if not isinstance(oldvalue, SessionStatus):
        return
    
    if oldvalue == value:
        return  # Статус не изменился
    
    print(f"""
╔══════════════════════════════════════════╗
║ 🔔 СОБЫТИЕ: session.status_changed       ║
║    Сессия ID: {target.id:<26} ║
║    Старый статус: {oldvalue.value:<20} ║
║    Новый статус: {value.value:<22} ║
║    Владелец ID: {target.owner_id:<24} ║
╚══════════════════════════════════════════╝
    """)
    
    # Специфические реакции на конкретные переходы
    transition_key = f"{oldvalue.value}→{value.value}"
    
    if transition_key == "editing→voting":
        _on_voting_started(target)
    elif transition_key == "voting→results":
        _on_voting_completed(target)
    elif transition_key == "results→closed":
        _on_session_closed(target)


def _on_voting_started(session: Session):
    """Реакция на начало голосования."""
    print(f"   🗳️ Голосование началось для сессии #{session.id}")
    print(f"   ⏱️ Длительность: {session.voting_duration}")
    
    # Оповещение через WebSocket
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            from app.websocket.manager import manager
            asyncio.create_task(
                manager.broadcast_to_session(
                    session.id,
                    {
                        "type": "voting_started",
                        "payload": {
                            "session_id": session.id,
                            "voting_ends_at": session.voting_ends_at.isoformat() if session.voting_ends_at else None
                        }
                    }
                )
            )
            print(f"   📡 WebSocket-уведомление отправлено")
    except Exception as e:
        print(f"   ⚠️ Не удалось отправить WebSocket: {e}")


def _on_voting_completed(session: Session):
    """Реакция на завершение голосования."""
    print(f"   🏆 Голосование завершено для сессии #{session.id}")
    
    if session.results_json:
        winner = session.results_json.get("winner", {})
        print(f"   🥇 Победитель: {winner.get('item_name', 'Неизвестно')}")
    
    # Оповещение через WebSocket
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            from app.websocket.manager import manager
            asyncio.create_task(
                manager.broadcast_to_session(
                    session.id,
                    {
                        "type": "results_ready",
                        "payload": session.results_json or {}
                    }
                )
            )
            print(f"   📡 WebSocket-уведомление с результатами отправлено")
    except Exception as e:
        print(f"   ⚠️ Не удалось отправить WebSocket: {e}")


def _on_session_closed(session: Session):
    """Реакция на закрытие лобби."""
    print(f"   🚪 Лобби #{session.id} закрыто")
    print(f"   👤 Закрыто пользователем #{session.closed_by}")


# ============================================================
# СОБЫТИЯ ДРУЗЕЙ
# ============================================================

@event.listens_for(Friend.status, 'set', active_history=True)
def on_friendship_status_changed(
    target: Friend,
    value: FriendStatus,
    oldvalue: FriendStatus,
    initiator
):
    """
    Событие: статус дружбы изменён.
    
    Отслеживаем:
    - PENDING → ACCEPTED (заявка принята)
    - PENDING → REJECTED (заявка отклонена)
    """
    if not isinstance(oldvalue, FriendStatus):
        return
    
    if oldvalue == value:
        return
    
    print(f"""
╔══════════════════════════════════════════╗
║ 🔔 СОБЫТИЕ: friendship.status_changed    ║
║    От: {target.user_id:<30} ║
║    Кому: {target.friend_id:<29} ║
║    Старый статус: {oldvalue.value:<20} ║
║    Новый статус: {value.value:<22} ║
╚══════════════════════════════════════════╝
    """)
    
    if value == FriendStatus.ACCEPTED:
        _on_friendship_accepted(target)
    elif value == FriendStatus.REJECTED:
        _on_friendship_rejected(target)


def _on_friendship_accepted(friendship: Friend):
    """Реакция на принятие заявки в друзья."""
    print(f"   🤝 Дружба подтверждена между #{friendship.user_id} и #{friendship.friend_id}")
    
    # Оповещение отправителя через WebSocket
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            from app.websocket.manager import manager
            asyncio.create_task(
                manager.send_to_user(
                    friendship.user_id,
                    {
                        "type": "friend_request_accepted",
                        "payload": {"friend_id": friendship.friend_id}
                    }
                )
            )
            print(f"   📡 Уведомление отправлено пользователю #{friendship.user_id}")
    except Exception as e:
        print(f"   ⚠️ Не удалось отправить WebSocket: {e}")


def _on_friendship_rejected(friendship: Friend):
    """Реакция на отклонение заявки в друзья."""
    print(f"   👋 Заявка отклонена: #{friendship.user_id} → #{friendship.friend_id}")


# ============================================================
# РЕГИСТРАЦИЯ ВСЕХ СОБЫТИЙ
# ============================================================

def register_all_events():
    """
    Регистрирует все обработчики событий.
    Вызывается при старте приложения.
    
    Фактически, обработчики уже зарегистрированы через декораторы @event.
    Эта функция — для явного импорта и гарантии, что все события загружены.
    """
    print("✅ Все обработчики событий зарегистрированы:")
    print("   - user.registered")
    print("   - session.status_changed")
    print("   - friendship.status_changed")