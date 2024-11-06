from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select, delete
import structlog

from models.referral import Referral, ReferralLink, PendingReferral
from utils.referral import create_ref_link, get_user_ref_link
from models.enums import RewardType
from utils.rewards import give_reward, process_reward

from filters.chat_type import ChatTypeFilter
from filters.referral import ReferralCommandFilter
from keyboards.subscription import get_subscription_keyboard

router = Router()
router.message.filter(ChatTypeFilter(["private"]))
logger = structlog.get_logger()

REFERRAL_PRIORITIES = {
    "START": 8,
    "MANAGE": 7,
    "INFO": 6
}

async def process_referral(
    session: AsyncSession, 
    ref_code: str, 
    new_user_id: int,
    message: Message
) -> Optional[Referral]:
    """Обрабатывает переход по реферальной ссылке"""
    # Находим ссылку по коду
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
    await session.flush()  # Получаем id реферала
    
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
            ref_link.user_id,  # Награду получает пригласивший
            referral.id,
            RewardType.CHAPTER_UNLOCK,
            "1"  # Номер главы для разблокировки
        )
        
        # Обрабатываем награду
        success = await process_reward(session, reward)
        if success:
            await message.bot.send_message(
                ref_link.user_id,  # Отправляем сообщение пригласившему
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
        # Продолжаем выполнение, так как реферал уже создан
    
    await session.commit()
    return referral

@router.message(Command("ref"))
async def cmd_get_ref_link(message: Message, session: AsyncSession):
    """Получение реферальной ссылки"""
    try:
        # Сначала пытаемся найти существующую ссылку
        ref_link = await get_user_ref_link(session, message.from_user.id)
        if not ref_link:
            # Создаем новую только если не нашли существующую
            ref_link = await create_ref_link(session, message.from_user.id)
            await session.commit()
            
        bot_username = (await message.bot.me()).username
        invite_link = f"https://t.me/{bot_username}?start=ref_{ref_link.code}"
        
        await logger.ainfo(
            "Generated referral link",
            user_id=message.from_user.id,
            username=message.from_user.username,
            ref_code=ref_link.code
        )
        
        await message.answer(f"Ваша реферальная ссылка: {invite_link}")
    except Exception as e:
        await logger.aerror(
            "Error generating referral link",
            user_id=message.from_user.id,
            error=str(e)
        )
        await session.rollback()
        await message.answer(
            "Произошла ошибка при создании реферальной ссылки",
            parse_mode="HTML"
        )

@router.message(
    Command("start"),
    ReferralCommandFilter(),
    flags={"priority": REFERRAL_PRIORITIES["START"]}
)
async def cmd_start_with_ref(message: Message, session: AsyncSession, l10n):
    """Обработка только реферальных команд /start ref_code"""
    args = message.text.split()
    ref_code = args[1][4:]  # Убираем префикс 'ref_'
    
    # Проверяем, не был ли уже этот пользователь приглашен
    existing = await session.execute(
        select(Referral).where(Referral.referred_id == message.from_user.id)
    )
    if existing.scalar_one_or_none():
        await logger.ainfo(
            "User already referred",
            user_id=message.from_user.id
        )
        await message.answer(
            l10n.format_value("hello-msg"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return

    # Проверяем существование реферальной ссылки
    result = await session.execute(
        select(ReferralLink).where(ReferralLink.code == ref_code)
    )
    ref_link = result.scalar_one_or_none()
    
    if not ref_link or ref_link.user_id == message.from_user.id:
        await logger.ainfo(
            "Invalid referral link or self-referral",
            ref_code=ref_code,
            user_id=message.from_user.id,
            ref_link_user_id=ref_link.user_id if ref_link else None
        )
        await message.answer(
            l10n.format_value("hello-msg"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    await logger.ainfo(
        "Saving pending referral",
        ref_code=ref_code,
        user_id=message.from_user.id,
        username=message.from_user.username
    )
    
    # Удаляем старые pending referrals для этого пользователя
    await session.execute(
        delete(PendingReferral).where(PendingReferral.user_id == message.from_user.id)
    )
    await session.commit()
    
    # Сохраняем код для последующего применения
    pending = PendingReferral(
        user_id=message.from_user.id,
        ref_code=ref_code
    )
    session.add(pending)
    await session.commit()
    
    # Показываем стандартное приветствие с кнопкой подписки
    await message.answer(
        l10n.format_value("hello-msg"),
        reply_markup=await get_subscription_keyboard(message),
        parse_mode="HTML"
    )
