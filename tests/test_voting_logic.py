import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.session_service import SessionService
from app.models.session import Session, SessionParticipant, SessionStatus, SessionMode, SessionList
from app.models.list import ListItem


class TestVotingLogic:
"""Тесты для логики подсчета голосов."""

@pytest.fixture
def mock_db(self):
    return AsyncMock()

@pytest.fixture
def sample_items(self):
    return [
        ListItem(id=1, name="Item 1", list_id=1, order_index=0),
        ListItem(id=2, name="Item 2", list_id=1, order_index=1),
        ListItem(id=3, name="Item 3", list_id=1, order_index=2),
        ListItem(id=4, name="Item 4", list_id=1, order_index=3),
    ]

@pytest.fixture
def sample_session(self, sample_items):
    """Создаём сессию БЕЗ вызова конструктора SQLAlchemy."""
    session = MagicMock(spec=Session)
    session.id = 1
    session.mode = SessionMode.RANKING
    session.status = SessionStatus.VOTING
    session.participants = []
    
    # Мокаем активный список
    active_list = MagicMock(spec=SessionList)
    active_list.items = sample_items
    session.item_list = active_list
    
    # Добавляем list_service как MagicMock
    session.list_service = MagicMock()
    session.list_service.get_active_list = AsyncMock(return_value=active_list)
    
    return session

def _run_async(self, coro):
    """Вспомогательный метод для запуска асинхронных методов."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def test_ranking_single_vote(self, mock_db, sample_session):
    """Тест 1: Один голос - победитель должен быть первым в его списке."""
    service = SessionService(mock_db)
    service.list_service.get_active_list = AsyncMock(
        return_value=sample_session.item_list
    )
    
    participant = SessionParticipant(
        user_id=1,
        has_voted=True,
        vote_data={"ranked_ids": [1, 2, 3, 4]}
    )
    sample_session.participants = [participant]
    
    results = self._run_async(
        service._calculate_ranking_results(sample_session, sample_session.item_list)
    )
    
    assert results["winner"]["item_id"] == 1
    assert results["results"][0]["total_score"] == 4
    assert results["results"][1]["total_score"] == 3
    assert results["results"][2]["total_score"] == 2
    assert results["results"][3]["total_score"] == 1

def test_ranking_multiple_votes_same_winner(self, mock_db, sample_session):
    """Тест 2: Два голоса с одинаковым победителем."""
    service = SessionService(mock_db)
    service.list_service.get_active_list = AsyncMock(
        return_value=sample_session.item_list
    )
    
    participants = [
        SessionParticipant(user_id=1, has_voted=True,
            vote_data={"ranked_ids": [1, 2, 3, 4]}),
        SessionParticipant(user_id=2, has_voted=True,
            vote_data={"ranked_ids": [1, 3, 2, 4]})
    ]
    sample_session.participants = participants
    
    results = self._run_async(
        service._calculate_ranking_results(sample_session, sample_session.item_list)
    )
    
    assert results["winner"]["item_id"] == 1
    assert results["results"][0]["total_score"] == 8

def test_ranking_different_winners(self, mock_db, sample_session):
    """Тест 3: Разные победители."""
    service = SessionService(mock_db)
    service.list_service.get_active_list = AsyncMock(
        return_value=sample_session.item_list
    )
    
    participants = [
        SessionParticipant(user_id=1, has_voted=True,
            vote_data={"ranked_ids": [1, 2, 3, 4]}),
        SessionParticipant(user_id=2, has_voted=True,
            vote_data={"ranked_ids": [2, 1, 3, 4]})
    ]
    sample_session.participants = participants
    
    results = self._run_async(
        service._calculate_ranking_results(sample_session, sample_session.item_list)
    )
    
    scores = {r["item_id"]: r["total_score"] for r in results["results"]}
    assert scores[1] == 7
    assert scores[2] == 7
    assert scores[3] == 4
    assert scores[4] == 2

def test_ranking_complex_scenario(self, mock_db, sample_session):
    """Тест 5: Комплексный сценарий."""
    service = SessionService(mock_db)
    service.list_service.get_active_list = AsyncMock(
        return_value=sample_session.item_list
    )
    
    participants = [
        SessionParticipant(user_id=1, has_voted=True, vote_data={"ranked_ids": [1, 2, 3, 4]}),
        SessionParticipant(user_id=2, has_voted=True, vote_data={"ranked_ids": [1, 3, 2, 4]}),
        SessionParticipant(user_id=3, has_voted=True, vote_data={"ranked_ids": [2, 1, 4, 3]}),
        SessionParticipant(user_id=4, has_voted=True, vote_data={"ranked_ids": [3, 4, 1, 2]}),
        SessionParticipant(user_id=5, has_voted=True, vote_data={"ranked_ids": [4, 3, 2, 1]}),
    ]
    sample_session.participants = participants
    
    results = self._run_async(
        service._calculate_ranking_results(sample_session, sample_session.item_list)
    )
    
    expected_scores = {1: 14, 2: 12, 3: 13, 4: 11}
    for r in results["results"]:
        assert r["total_score"] == expected_scores[r["item_id"]]
    assert results["winner"]["item_id"] == 1

def test_validation_duplicate_ids(self, mock_db):
    """Тест 7: Валидация дубликатов ID."""
    from app.schemas.session import VoteRequest
    with pytest.raises(ValueError, match="Duplicate item IDs"):
        VoteRequest(ranked_item_ids=[1, 2, 2, 3])

def test_random_mode(self, mock_db, sample_session):
    """Тест 6: Режим случайного выбора."""
    import random
    random.seed(42)
    
    sample_session.mode = SessionMode.RANDOM
    service = SessionService(mock_db)
    
    results = self._run_async(
        service._calculate_random_results(sample_session, sample_session.item_list)
    )
    
    assert "winner" in results
    assert results["winner"]["place"] == 1
    assert results["winner"]["total_score"] == 1