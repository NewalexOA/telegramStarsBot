from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

# Тип для сущности
T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Базовый класс репозитория
    T - тип сущности, с которой работает репозиторий
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._model = self.get_model()
    
    @abstractmethod
    def get_model(self) -> type[T]:
        """Возвращает класс модели"""
        pass
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Получение записи по ID"""
        result = await self._session.execute(
            select(self._model).where(self._model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[T]:
        """Получение всех записей"""
        result = await self._session.execute(select(self._model))
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> T:
        """Создание новой записи"""
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """Обновление записи"""
        query = (
            update(self._model)
            .where(self._model.id == id)
            .values(**kwargs)
            .returning(self._model)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
    
    async def delete(self, id: int) -> bool:
        """Удаление записи"""
        query = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(query)
        return result.rowcount > 0
    
    async def filter_by(self, **kwargs) -> List[T]:
        """Фильтрация по указанным параметрам"""
        query = select(self._model)
        for key, value in kwargs.items():
            query = query.where(getattr(self._model, key) == value)
        result = await self._session.execute(query)
        return list(result.scalars().all()) 