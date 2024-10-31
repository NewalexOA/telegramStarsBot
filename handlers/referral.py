from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from utils.referral import create_ref_link, get_user_ref_link, process_referral

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
        referral = await process_referral(session, ref_code, message.from_user.id)
        if referral:
            # Уведомляем пригласившего
            await message.bot.send_message(
                referral.referrer_id,
                "По вашей ссылке присоединился новый пользователь! "
                "Вам открыта новая глава!"
            )
            # Приветствуем нового пользователя
            await message.answer("Добро пожаловать! Вы присоединились по реферальной ссылке.")
        else:
            await message.answer("Добро пожаловать!")
    else:
        await message.answer("Добро пожаловать!") 