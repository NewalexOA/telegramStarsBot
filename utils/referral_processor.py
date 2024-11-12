import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message

from models.referral import Referral, ReferralLink

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
    
    # Подсчитываем количество рефералов после успешного добавления
    referral_count = await session.scalar(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == ref_link.user_id)
    )
    
    # Определяем текст сообщения о награде
    reward_text = "Поздравляем! "
    if referral_count == 1:
        reward_text += "Вы получили скидку 30% на перезапуск истории!"
    elif referral_count == 2:
        reward_text += "Вы получили скидку 40% на перезапуск истории!"
    elif referral_count == 3:
        reward_text += "Вы получили максимальную скидку 50% на перезапуск истории!"
    
    await message.bot.send_message(
        ref_link.user_id,
        reward_text
    )
    
    await session.commit()
    return referral 