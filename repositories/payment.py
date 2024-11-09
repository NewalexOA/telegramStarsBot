from typing import List
from sqlalchemy import select, func
from .base import BaseRepository
from models.payment import Payment

class PaymentRepository(BaseRepository[Payment]):
    """Репозиторий для работы с платежами"""
    
    def get_model(self) -> type[Payment]:
        return Payment
        
    async def get_by_user_id(self, user_id: int) -> List[Payment]:
        """Получение всех платежей пользователя"""
        result = await self._session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())
        
    async def count_all(self) -> int:
        """Подсчет всех платежей"""
        result = await self._session.execute(
            select(func.count(Payment.id))
        )
        return result.scalar()
        
    async def get_total_amount(self) -> int:
        """Получение общей суммы платежей"""
        result = await self._session.execute(
            select(func.sum(Payment.amount))
        )
        return result.scalar() or 0 