from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from repositories.novel import NovelRepository, NovelMessageRepository
from repositories.referral import (
    ReferralRepository, 
    ReferralLinkRepository,
    PendingReferralRepository,
    ReferralRewardRepository
)
from repositories.payment import PaymentRepository

logger = structlog.get_logger()

class UnitOfWork:
    """Unit of Work паттерн для управления транзакциями и репозиториями"""
    
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        
    async def __aenter__(self):
        logger.debug("Opening new UnitOfWork")
        self.session = self._session_factory()
        
        # Инициализация репозиториев
        self.novels = NovelRepository(self.session)
        self.novel_messages = NovelMessageRepository(self.session)
        self.referrals = ReferralRepository(self.session)
        self.referral_links = ReferralLinkRepository(self.session)
        self.pending_referrals = PendingReferralRepository(self.session)
        self.referral_rewards = ReferralRewardRepository(self.session)
        self.payments = PaymentRepository(self.session)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                "Error in UnitOfWork, rolling back",
                error=str(exc_val),
                exc_info=True
            )
            await self.rollback()
        await self.session.close()
        logger.debug("Closed UnitOfWork")
        
    async def commit(self):
        """Фиксация изменений"""
        try:
            await self.session.commit()
            logger.debug("Committed UnitOfWork")
        except Exception as e:
            logger.error(f"Error committing UnitOfWork: {e}")
            await self.rollback()
            raise
        
    async def rollback(self):
        """Откат изменений"""
        try:
            await self.session.rollback()
            logger.debug("Rolled back UnitOfWork")
        except Exception as e:
            logger.error(f"Error rolling back UnitOfWork: {e}")
            raise 