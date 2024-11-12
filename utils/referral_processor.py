import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message

from models.referral import Referral, ReferralLink, PendingReferral

logger = structlog.get_logger()

async def process_pending_referral(user_id: int, session: AsyncSession, message: Message) -> None:
    """Обрабатывает отложенный реферал после подписки на канал"""
    # Находим pending реферал
    result = await session.execute(
        select(PendingReferral)
        .where(PendingReferral.user_id == user_id)
        .order_by(PendingReferral.created_at.desc())
    )
    pending = result.scalar_one_or_none()
    
    if not pending:
        return
        
    try:
        # Находим ссылку по коду
        result = await session.execute(
            select(ReferralLink).where(ReferralLink.code == pending.ref_code)
        )
        ref_link = result.scalar_one_or_none()
        
        if not ref_link or ref_link.user_id == user_id:
            await logger.ainfo(
                "Invalid referral link or self-referral",
                ref_code=pending.ref_code,
                user_id=user_id
            )
            return
        
        # Проверяем, не был ли уже этот пользователь приглашен
        existing = await session.execute(
            select(Referral).where(Referral.referred_id == user_id)
        )
        if existing.scalar_one_or_none():
            await logger.ainfo(
                "User already referred",
                user_id=user_id
            )
            return
        
        # Создаем запись о реферале
        referral = Referral(
            referrer_id=ref_link.user_id,
            referred_id=user_id,
            link_id=ref_link.id
        )
        session.add(referral)
        await session.flush()
        
        # Подсчитываем количество рефералов
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
        
        # Удаляем pending реферал
        await session.delete(pending)
        await session.commit()
        
        await logger.ainfo(
            "Processed pending referral after subscription",
            user_id=user_id,
            ref_code=pending.ref_code,
            success=True
        )
    except Exception as e:
        logger.error(
            "Error processing pending referral",
            user_id=user_id,
            error=str(e)
        )
