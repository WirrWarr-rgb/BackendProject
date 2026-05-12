"""
Value Objects для проекта.
Value Object - объект без собственного ID, определяемый значениями полей.
"""

class VotingDuration:
    """
    Value Object для длительности голосования.
    
    Хранит секунды, предоставляет методы для конвертации и форматирования.
    Аналог "перевод рублей в копейки" - конвертация секунд в минуты.
    """
    
    MIN_SECONDS = 30    # Минимум 30 секунд
    MAX_SECONDS = 600   # Максимум 10 минут
    
    def __init__(self, seconds: int):
        """
        Создаёт VotingDuration из секунд.
        
        Args:
            seconds: длительность в секундах (30-600)
            
        Raises:
            ValueError: если секунды вне допустимого диапазона
        """
        if not isinstance(seconds, int):
            raise ValueError(f"Seconds must be integer, got {type(seconds)}")
        if seconds < self.MIN_SECONDS:
            raise ValueError(
                f"Voting duration must be at least {self.MIN_SECONDS} seconds, got {seconds}"
            )
        if seconds > self.MAX_SECONDS:
            raise ValueError(
                f"Voting duration cannot exceed {self.MAX_SECONDS} seconds, got {seconds}"
            )
        self._seconds = seconds
    
    @property
    def seconds(self) -> int:
        """Получить длительность в секундах"""
        return self._seconds
    
    @property
    def minutes(self) -> float:
        """Конвертировать секунды в минуты"""
        return self._seconds / 60
    
    @property
    def minutes_int(self) -> int:
        """Получить целое количество минут"""
        return self._seconds // 60
    
    @property
    def remaining_seconds(self) -> int:
        """Получить оставшиеся секунды (после вычитания полных минут)"""
        return self._seconds % 60
    
    def to_formatted_string(self) -> str:
        """
        Красивое отображение длительности.
        
        Returns:
            "2 мин 0 сек" или "45 сек"
        """
        if self.minutes_int > 0:
            return f"{self.minutes_int} мин {self.remaining_seconds} сек"
        return f"{self.seconds} сек"
    
    def to_dict(self) -> dict:
        """Сериализация в словарь"""
        return {
            "seconds": self.seconds,
            "minutes": round(self.minutes, 2),
            "formatted": self.to_formatted_string()
        }
    
    def __eq__(self, other) -> bool:
        """Два VO равны, если равны их значения"""
        if not isinstance(other, VotingDuration):
            return False
        return self._seconds == other._seconds
    
    def __hash__(self) -> int:
        return hash(self._seconds)
    
    def __repr__(self) -> str:
        return f"VotingDuration({self._seconds}s = {self.to_formatted_string()})"
    
    def __str__(self) -> str:
        return self.to_formatted_string()
    
    def __composite_values__(self):
        """
        Метод для SQLAlchemy Composite.
        Возвращает значения для сохранения в БД.
        """
        return (self._seconds,)
    
    @classmethod
    def from_seconds(cls, seconds: int) -> "VotingDuration":
        """Фабричный метод - создать из секунд"""
        return cls(seconds)