# tests/test_value_objects.py
import pytest
from app.models.value_objects import VotingDuration


class TestVotingDuration:
    """Тесты для Value Object VotingDuration."""
    
    def test_create_valid_duration(self):
        """Тест создания с валидными значениями."""
        # Минимальное значение
        d = VotingDuration(30)
        assert d.seconds == 30
        
        # Среднее значение
        d = VotingDuration(120)
        assert d.seconds == 120
        
        # Максимальное значение
        d = VotingDuration(600)
        assert d.seconds == 600
    
    def test_create_invalid_duration_too_small(self):
        """Тест: значение меньше минимального."""
        with pytest.raises(ValueError, match="at least 30"):
            VotingDuration(10)
        
        with pytest.raises(ValueError, match="at least 30"):
            VotingDuration(0)
    
    def test_create_invalid_duration_too_large(self):
        """Тест: значение больше максимального."""
        with pytest.raises(ValueError, match="cannot exceed 600"):
            VotingDuration(601)
        
        with pytest.raises(ValueError, match="cannot exceed 600"):
            VotingDuration(1000)
    
    def test_create_invalid_type(self):
        """Тест: передача неверного типа."""
        with pytest.raises(ValueError, match="must be integer"):
            VotingDuration("120")
        
        with pytest.raises(ValueError, match="must be integer"):
            VotingDuration(120.5)
    
    def test_seconds_to_minutes_conversion(self):
        """Тест конвертации секунд в минуты."""
        d = VotingDuration(120)
        assert d.minutes == 2.0
        assert d.minutes_int == 2
        assert d.remaining_seconds == 0
        
        d = VotingDuration(150)
        assert d.minutes == 2.5
        assert d.minutes_int == 2
        assert d.remaining_seconds == 30
        
        d = VotingDuration(45)
        assert d.minutes == 0.75
        assert d.minutes_int == 0
        assert d.remaining_seconds == 45
    
    def test_formatted_string(self):
        """Тест форматированного вывода."""
        # Только минуты
        d = VotingDuration(120)
        assert d.to_formatted_string() == "2 мин 0 сек"
        
        # Минуты и секунды
        d = VotingDuration(150)
        assert d.to_formatted_string() == "2 мин 30 сек"
        
        # Только секунды
        d = VotingDuration(45)
        assert d.to_formatted_string() == "45 сек"
        
        # Одна минута
        d = VotingDuration(60)
        assert d.to_formatted_string() == "1 мин 0 сек"
    
    def test_equality(self):
        """Тест равенства Value Objects."""
        d1 = VotingDuration(120)
        d2 = VotingDuration(120)
        d3 = VotingDuration(150)
        
        # Одинаковые значения — равны
        assert d1 == d2
        
        # Разные значения — не равны
        assert d1 != d3
        
        # Сравнение с другим типом
        assert d1 != 120
        assert d1 != "120"
    
    def test_hash(self):
        """Тест хеширования (для использования в словарях)."""
        d1 = VotingDuration(120)
        d2 = VotingDuration(120)
        
        # Одинаковые значения — одинаковый хеш
        assert hash(d1) == hash(d2)
        
        # Можно использовать как ключ словаря
        cache = {d1: "value"}
        assert cache[d2] == "value"
    
    def test_to_dict(self):
        """Тест сериализации в словарь."""
        d = VotingDuration(150)
        result = d.to_dict()
        
        assert result["seconds"] == 150
        assert result["minutes"] == 2.5
        assert result["formatted"] == "2 мин 30 сек"
    
    def test_repr(self):
        """Тест строкового представления."""
        d = VotingDuration(120)
        repr_str = repr(d)
        
        assert "VotingDuration" in repr_str
        assert "120" in repr_str
        assert "2 мин 0 сек" in repr_str
    
    def test_composite_values(self):
        """Тест метода для SQLAlchemy Composite."""
        d = VotingDuration(120)
        values = d.__composite_values__()
        
        assert values == (120,)
        assert len(values) == 1
        assert values[0] == 120
    
    def test_from_seconds_factory(self):
        """Тест фабричного метода."""
        d = VotingDuration.from_seconds(90)
        assert d.seconds == 90
        assert d.to_formatted_string() == "1 мин 30 сек"