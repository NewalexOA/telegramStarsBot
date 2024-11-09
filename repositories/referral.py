from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, delete, distinct

from .base import BaseRepository
from models.referral import ReferralLink, Referral, PendingReferral, ReferralReward

class ReferralLinkRepository(BaseRepository[ReferralLink]):
    """Репозиторий для работы с реферальными ссылками"""
    
    def get_model(self) -> type[ReferralLink]:
        return ReferralLink
    
    async def get_by_user_id(self, user_id: int) -> Optional[ReferralLink]:
        """Получение реферальной ссылки по ID пользователя"""
        result = await self._session.execute(
            select(ReferralLink).where(ReferralLink.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[ReferralLink]:
        """Получение реферальной ссылки по коду"""
        result = await self._session.execute(
            select(ReferralLink).where(ReferralLink.code == code)
        )
        return result.scalar_one_or_none()

class ReferralRepository(BaseRepository[Referral]):
    """Репозиторий для работы с рефералами"""
    
    def get_model(self) -> type[Referral]:
        return Referral
    
    async def get_by_referred_id(self, referred_id: int) -> Optional[Referral]:
        """Получение реферала по ID приглашенного пользователя"""
        result = await self._session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()
    
    async def get_referrer_stats(self, referrer_id: int) -> tuple[int, int]:
        """Получение статистики рефералов для реферера"""
        result = await self._session.execute(
            select(
                func.count(Referral.id).label('total_referrals'),
                func.count(ReferralReward.id).label('total_rewards')
            )
            .select_from(Referral)
            .outerjoin(ReferralReward)
            .where(Referral.referrer_id == referrer_id)
        )
        return result.one()

    async def get_by_referrer_id(self, referrer_id: int) -> List[Referral]:
        """Получение всех рефералов по ID реферера"""
        result = await self._session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        return list(result.scalars().all())

    async def delete_by_user_id(self, user_id: int) -> None:
        """Удаление всех ожидающих рефералов пользователя"""
        await self._session.execute(
            delete(PendingReferral).where(PendingReferral.user_id == user_id)
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Получение общей статистики рефералов"""
        result = await self._session.execute(
            select(
                func.count(distinct(Referral.referrer_id)).label('active_referrers'),
                func.count(Referral.id).label('total_referrals')
            )
        )
        row = result.one()
        return {
            'active_referrers': row.active_referrers,
            'total_referrals': row.total_referrals
        }

class PendingReferralRepository(BaseRepository[PendingReferral]):
    """Репозиторий для работы с ожидающими рефералами"""
    
    def get_model(self) -> type[PendingReferral]:
        return PendingReferral
    
    async def get_by_user_id(self, user_id: int) -> Optional[PendingReferral]:
        """Получение ожидающего реферала по ID пользователя"""
        result = await self._session.execute(
            select(PendingReferral)
            .where(PendingReferral.user_id == user_id)
            .order_by(PendingReferral.created_at.desc())
        )
        return result.scalar_one_or_none()

class ReferralRewardRepository(BaseRepository[ReferralReward]):
    """Репозиторий для работы с наградами за рефералов"""
    
    def get_model(self) -> type[ReferralReward]:
        return ReferralReward
    
    async def get_user_rewards(self, user_id: int) -> List[ReferralReward]:
        """Получение всех наград пользователя"""
        result = await self._session.execute(
            select(ReferralReward)
            .where(ReferralReward.user_id == user_id)
            .order_by(ReferralReward.created_at.desc())
        )
        return list(result.scalars().all()) 