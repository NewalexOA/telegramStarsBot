from typing import Optional, List
from sqlalchemy import select, func, distinct, and_

from .base import BaseRepository
from models.novel import NovelState, NovelMessage

class NovelRepository(BaseRepository[NovelState]):
    """Репозиторий для работы с состояниями новелл"""
    
    def get_model(self) -> type[NovelState]:
        return NovelState
    
    async def get_by_user_id(self, user_id: int) -> Optional[NovelState]:
        """Получение состояния новеллы по ID пользователя"""
        result = await self._session.execute(
            select(NovelState).where(NovelState.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_novels(self) -> List[NovelState]:
        """Получение всех активных новелл"""
        result = await self._session.execute(
            select(NovelState)
            .where(NovelState.is_completed.is_(False))
            .order_by(NovelState.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_stats(self) -> tuple[int, int, int]:
        """Получение статистики новелл"""
        result = await self._session.execute(
            select(
                func.count(NovelState.user_id.distinct()).label('total_users'),
                func.count(NovelState.id).filter(NovelState.is_completed.is_(False)).label('active_novels'),
                func.count(NovelState.id).filter(NovelState.is_completed.is_(True)).label('completed_novels')
            )
        )
        return result.one()

    async def count_unique_users(self) -> int:
        """Подсчет уникальных пользователей"""
        result = await self._session.execute(
            select(func.count(distinct(NovelState.user_id)))
        )
        return result.scalar()

    async def count_active(self) -> int:
        """Подсчет активных новелл"""
        result = await self._session.execute(
            select(func.count())
            .where(and_(
                NovelState.is_completed.is_(False),
                NovelState.needs_payment.is_(False)
            ))
        )
        return result.scalar()

    async def count_completed(self) -> int:
        """Подсчет завершенных новелл"""
        result = await self._session.execute(
            select(func.count())
            .where(NovelState.is_completed.is_(True))
        )
        return result.scalar()

class NovelMessageRepository(BaseRepository[NovelMessage]):
    """Репозиторий для работы с сообщениями новелл"""
    
    def get_model(self) -> type[NovelMessage]:
        return NovelMessage
    
    async def get_novel_messages(self, novel_state_id: int) -> List[NovelMessage]:
        """Получение всех сообщений новеллы"""
        result = await self._session.execute(
            select(NovelMessage)
            .where(NovelMessage.novel_state_id == novel_state_id)
            .order_by(NovelMessage.created_at)
        )
        return list(result.scalars().all())
    
    async def get_last_assistant_message(self, novel_state_id: int) -> Optional[NovelMessage]:
        """Получение последнего сообщения ассистента"""
        result = await self._session.execute(
            select(NovelMessage)
            .where(
                NovelMessage.novel_state_id == novel_state_id,
                NovelMessage.is_user.is_(False)
            )
            .order_by(NovelMessage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none() 