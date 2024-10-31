from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select

from models.referral import Referral, ReferralLink
from utils.referral import create_ref_link, get_user_ref_link
from models.enums import RewardType
from utils.rewards import give_reward, process_reward

router = Router()

@router.message(Command("ref", "invite"))
async def cmd_get_ref_link(message: Message, session: AsyncSession):
    """Получить реферальную ссылку"""
    ref_link = await get_user_ref_link(session, message.from_user.id)
    if not ref_link:
        ref_link = await create_ref_link(session, message.from_user.id)
    
    bot_username = (await message.bot.me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{ref_link.code}"
    
    await message.answer(
        f"Ваша реферальная ссылка:\n{invite_link}\n\n"
        "За каждого приглашенного пользователя вы получите доступ к новой главе!"
    )

@router.message(Command("start"))
async def cmd_start_with_ref(message: Message, session: AsyncSession):
    """Обработка перехода по реферальной ссылке"""
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        ref_code = args[1][4:]  # Убираем префикс 'ref_'
        referral = await process_referral(session, ref_code, message.from_user.id, message)
        if referral:
            # Приветствуем нового пользователя
            await message.answer("Добро пожаловать! Вы присоединились по реферальной ссылке.")
        else:
            await message.answer("Добро пожаловать!")
    else:
        await message.answer("Добро пожаловать!")

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
        return None
    
    # Создаем запись о реферале
    referral = Referral(
        referrer_id=ref_link.user_id,
        referred_id=new_user_id,
        link_id=ref_link.id
    )
    session.add(referral)
    await session.commit()
    
    # Выдаем награду за реферала
    reward = await give_reward(
        session,
        referral.referrer_id,
        referral.id,
        RewardType.CHAPTER_UNLOCK,
        "1"  # Номер главы для разблокировки
    )
    
    # Обрабатываем награду
    success = await process_reward(session, reward)
    if success:
        await message.bot.send_message(
            referral.referrer_id,
            "Поздравляем! Вам открыта новая глава за приглашение друга!"
        )
    
    return referral