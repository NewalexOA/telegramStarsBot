from typing import Optional, List
import structlog
from aiogram.types import Message
from unit_of_work.unit_of_work import UnitOfWork
from models.referral import ReferralLink, Referral, PendingReferral, ReferralReward

logger = structlog.get_logger()

class ReferralService:
    """Сервис для работы с реферальной системой"""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_referral_link(self, user_id: int) -> ReferralLink:
        """Создание реферальной ссылки для пользователя"""
        async with self.uow as uow:
            # Проверяем существующую ссылку
            existing_link = await uow.referral_links.get_by_user_id(user_id)
            if existing_link:
                return existing_link
                
            # Создаем новую ссылку
            link = await uow.referral_links.create(
                user_id=user_id,
                code=self._generate_ref_code()
            )
            await uow.commit()
            
            logger.info(
                "Created referral link",
                user_id=user_id,
                code=link.code
            )
            return link

    async def process_referral(
        self, 
        referrer_id: int, 
        referred_id: int
    ) -> Optional[PendingReferral]:
        """Обработка реферального перехода"""
        async with self.uow as uow:
            # Проверяем существующие рефералы
            existing = await uow.referrals.get_by_referred_id(referred_id)
            if existing:
                logger.info(
                    "User already has referrer",
                    referred_id=referred_id,
                    referrer_id=existing.referrer_id
                )
                return None
                
            # Создаем ожидающий реферал
            pending = await uow.pending_referrals.create(
                user_id=referred_id,
                referrer_id=referrer_id
            )
            await uow.commit()
            
            logger.info(
                "Created pending referral",
                referrer_id=referrer_id,
                referred_id=referred_id
            )
            return pending

    async def confirm_referral(
        self, 
        pending: PendingReferral,
        reward_type: str
    ) -> Referral:
        """Подтверждение реферала и выдача награды"""
        async with self.uow as uow:
            # Создаем подтвержденный реферал
            referral = await uow.referrals.create(
                referrer_id=pending.referrer_id,
                referred_id=pending.user_id
            )
            
            # Создаем награду
            await uow.referral_rewards.create(
                user_id=pending.referrer_id,
                reward_type=reward_type,
                referral_id=referral.id
            )
            
            # Удаляем ожидающий реферал
            await uow.pending_referrals.delete(pending.id)
            await uow.commit()
            
            logger.info(
                "Confirmed referral",
                referral_id=referral.id,
                reward_type=reward_type
            )
            return referral

    async def get_user_stats(self, user_id: int) -> dict:
        """Получение статистики пользователя"""
        async with self.uow as uow:
            referrals = await uow.referrals.get_by_referrer_id(user_id)
            rewards = await uow.referral_rewards.get_user_rewards(user_id)
            
            return {
                "total_referrals": len(referrals),
                "total_rewards": len(rewards),
                "rewards_by_type": self._group_rewards_by_type(rewards)
            }

    def _generate_ref_code(self) -> str:
        """Генерация уникального кода для реферальной ссылки"""
        import uuid
        return str(uuid.uuid4())[:8]

    def _group_rewards_by_type(self, rewards: List[ReferralReward]) -> dict:
        """Группировка наград по типу"""
        result = {}
        for reward in rewards:
            if reward.reward_type not in result:
                result[reward.reward_type] = 0
            result[reward.reward_type] += 1
        return result 

    async def get_referral_link(self, ref_code: str) -> Optional[ReferralLink]:
        """Получение реферальной ссылки по коду"""
        async with self.uow as uow:
            return await uow.referral_links.get_by_code(ref_code)

    async def process_referral_start(
        self, 
        ref_code: str,
        new_user_id: int,
        message: Message
    ) -> Optional[PendingReferral]:
        """Обработка начального перехода по реферальной ссылке"""
        async with self.uow as uow:
            # Получаем ссылку
            ref_link = await uow.referral_links.get_by_code(ref_code)
            if not ref_link or ref_link.user_id == new_user_id:
                logger.info(
                    "Invalid referral link or self-referral",
                    ref_code=ref_code,
                    new_user_id=new_user_id
                )
                return None

            # Проверяем существующий реферал
            existing = await uow.referrals.get_by_referred_id(new_user_id)
            if existing:
                logger.info(
                    "User already has referrer",
                    new_user_id=new_user_id,
                    referrer_id=existing.referrer_id
                )
                return None

            # Создаем ожидающий реферал
            pending = await self.process_referral(
                ref_link.user_id,
                new_user_id
            )
            
            if pending:
                await message.bot.send_message(
                    ref_link.user_id,
                    "К вам пришел новый реферал! "
                    "После выполнения условий вы получите награду."
                )
                
            return pending

    async def confirm_referral_with_notification(
        self,
        pending: PendingReferral,
        reward_type: str,
        message: Message
    ) -> Optional[Referral]:
        """Подтверждение реферала с отправкой уведомления"""
        referral = await self.confirm_referral(pending, reward_type)
        if referral:
            await message.bot.send_message(
                referral.referrer_id,
                "Поздравляем! Вам открыта новая глава за приглашение друга!"
            )
        return referral

    async def get_by_referrer_id(self, referrer_id: int) -> List[Referral]:
        """Получение всех рефералов пользователя"""
        async with self.uow as uow:
            result = await uow.referrals.get_by_referrer_id(referrer_id)
            return result

    async def delete_pending_referrals(self, user_id: int) -> None:
        """Удаление всех ожидающих рефералов пользователя"""
        async with self.uow as uow:
            await uow.pending_referrals.delete_by_user_id(user_id)
            await uow.commit()