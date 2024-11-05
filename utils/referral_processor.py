import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message

from models.referral import Referral, ReferralLink
from utils.rewards import give_reward
from models.enums import RewardType

logger = structlog.get_logger()

async def process_referral(
    session: AsyncSession, 
    ref_code: str, 
    new_user_id: int,
    message: Message
) -> Referral | None:
    """Обрабатывает переход по реферальной ссылке"""
    result = await session.execute(
        select(ReferralLink).where(ReferralLink.code == ref_code)
    )
    ref_link = result.scalar_one_or_none()
    
    if not ref_link or ref_link.user_id == new_user_id:
        await logger.ainfo(
            "Invalid referral link or self-referral",
            ref_code=ref_code,
            new_user_id=new_user_id,
            ref_link_user_id=ref_link.user_id if ref_link else None
        )
        return None
    
    # Проверяем, не был ли уже этот пользователь приглашен
    existing = await session.execute(
        select(Referral).where(Referral.referred_id == new_user_id)
    )
    if existing.scalar_one_or_none():
        await logger.ainfo(
            "User already referred",
            new_user_id=new_user_id
        )
        return None
    
    # Создаем запись о реферале
    referral = Referral(
        referrer_id=ref_link.user_id,
        referred_id=new_user_id,
        link_id=ref_link.id
    )
    session.add(referral)
    await session.flush()
    
    await logger.ainfo(
        "Created referral record",
        referral_id=referral.id,
        referrer_id=referral.referrer_id,
        referred_id=referral.referred_id
    )
    
    # Выдаем награду за реферала
    try:
        reward = await give_reward(
            session,
            ref_link.user_id,
            referral.id,
            RewardType.CHAPTER_UNLOCK,
            "1"
        )
        
        if reward:
            await message.bot.send_message(
                ref_link.user_id,
                "Поздравляем! Вам открыта новая глава за приглашение друга!"
            )
            await logger.ainfo(
                "Reward processed successfully",
                reward_id=reward.id,
                user_id=ref_link.user_id
            )
    except Exception as e:
        await logger.aerror(
            "Error processing reward",
            error=str(e),
            user_id=ref_link.user_id,
            referral_id=referral.id
        )
    
    await session.commit()
    return referral 