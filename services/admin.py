import structlog
from typing import Dict, Any
from unit_of_work.unit_of_work import UnitOfWork

logger = structlog.get_logger()

class AdminService:
    """Сервис для административных функций"""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики бота"""
        try:
            async with self.uow as uow:
                # Статистика новелл
                total_users = await uow.novel_states.count_unique_users()
                active_novels = await uow.novel_states.count_active()
                completed_novels = await uow.novel_states.count_completed()
                
                # Статистика рефералов
                referral_stats = await uow.referrals.get_stats()
                
                # Статистика платежей
                total_payments = await uow.payments.count_all()
                total_amount = await uow.payments.get_total_amount()
                
                return {
                    "total_users": total_users,
                    "active_novels": active_novels,
                    "completed_novels": completed_novels,
                    "total_referrals": referral_stats['total_referrals'],
                    "active_referrers": referral_stats['active_referrers'],
                    "total_payments": total_payments,
                    "total_amount": total_amount
                }
        except Exception as exc:
            logger.error("Error getting stats", error=str(exc), exc_info=True)
            raise
    
    async def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """Получение детальной информации о пользователе"""
        try:
            async with self.uow as uow:
                novel_state = await uow.novel_states.get_by_user_id(user_id)
                referral_link = await uow.referral_links.get_by_user_id(user_id)
                referrals = await uow.referrals.get_by_referrer_id(user_id)
                rewards = await uow.referral_rewards.get_user_rewards(user_id)
                payments = await uow.payments.get_by_user_id(user_id)
                
                return {
                    "novel_state": novel_state,
                    "referral_link": referral_link,
                    "referrals": referrals,
                    "rewards": rewards,
                    "payments": payments
                }
        except Exception as exc:
            logger.error("Error getting user details", user_id=user_id, error=str(exc), exc_info=True)
            raise
    
    async def clear_database(self) -> None:
        """Очистка всей базы данных"""
        try:
            async with self.uow as uow:
                # Очистка таблиц новелл
                await uow.novel_states.clear()
                await uow.novel_messages.clear()
                
                # Очистка таблиц рефералов
                await uow.referrals.clear()
                await uow.referral_links.clear()
                await uow.referral_rewards.clear()
                await uow.pending_referrals.clear()
                
                # Очистка таблиц платежей
                await uow.payments.clear()
                
                await uow.commit()
                logger.info("Database cleared")
        except Exception as exc:
            logger.error("Error clearing database", error=str(exc), exc_info=True)
            await uow.rollback()
            raise