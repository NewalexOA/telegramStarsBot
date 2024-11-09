from abc import ABC, abstractmethod
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

class DatabaseInterface(ABC):
    """Базовый интерфейс для работы с базой данных"""
    
    @abstractmethod
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии базы данных"""
        pass
    
    @abstractmethod
    async def create_all(self) -> None:
        """Создание всех таблиц"""
        pass
    
    @abstractmethod
    async def drop_all(self) -> None:
        """Удаление всех таблиц"""
        pass 