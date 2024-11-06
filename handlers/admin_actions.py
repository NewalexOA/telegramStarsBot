import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsAdminFilter
from services.novel import NovelService
from keyboards.menu import get_main_menu
from models.referral import Referral

logger = structlog.get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["private"]))
router.message.filter(IsAdminFilter(is_admin=True))

@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """Проверка работоспособности бота"""
    await message.answer("Pong!")

@router.message(Command("get_id"))
async def cmd_get_id(message: Message):
    """Получение ID пользователя/чата"""
    await message.answer(
        f"User ID: {message.from_user.id}\n"
        f"Chat ID: {message.chat.id}"
    )

@router.message(Command("end_novel"))
async def cmd_end_novel(message: Message, session: AsyncSession, l10n):
    """Команда для принудительного завершения новеллы админом"""
    novel_service = NovelService(session)
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    if novel_state:
        await novel_service.end_story(novel_state, message)
        await message.answer(
            "Новелла завершена",
            reply_markup=get_main_menu(has_active_novel=False)
        )
    else:
        await message.answer("У вас нет активной новеллы")

@router.message(F.text == "📊 Статистика")
async def show_stats(message: Message, session: AsyncSession):
    """Показывает статистику реферальной программы"""
    try:
        # Получаем общее количество рефералов
        total_referrals = await session.scalar(
            select(func.count()).select_from(Referral)
        )
        
        # Получаем количество уникальных рефереров
        unique_referrers = await session.scalar(
            select(func.count(func.distinct(Referral.referrer_id))).select_from(Referral)
        )
        
        # Получаем топ-5 рефереров
        top_referrers_query = select(
            Referral.referrer_id,
            func.count().label('ref_count')
        ).group_by(
            Referral.referrer_id
        ).order_by(
            func.count().desc()
        ).limit(5)
        
        top_referrers = await session.execute(top_referrers_query)
        
        # Формируем сообщение
        stats_message = (
            "📊 Статистика реферальной программы:\n\n"
            f"Всего рефералов: {total_referrals}\n"
            f"Уникальных рефереров: {unique_referrers}\n\n"
            "Топ-5 рефереров:\n"
        )
        
        for referrer_id, count in top_referrers:
            stats_message += f"ID {referrer_id}: {count} рефералов\n"
        
        await message.answer(stats_message)
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer("Произошла ошибка при получении статистики")
