import os
import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select, func

from filters.is_admin import IsAdminFilter
from services.novel import NovelService
from keyboards.menu import get_main_menu
from models.referral import Referral
from models.base import Base

logger = structlog.get_logger()

router = Router()
router.message.filter(IsAdminFilter(is_admin=True))
router.callback_query.filter(IsAdminFilter(is_admin=True))

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
async def menu_stats(message: Message, session: AsyncSession):
    """Показывает статистику реферальной программы"""
    logger.info(f"Stats requested by admin {message.from_user.id}")
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
        
        await message.answer(
            stats_message,
            reply_markup=get_main_menu(is_admin=True)
        )
        logger.info(f"Stats sent to admin {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при получении статистики",
            reply_markup=get_main_menu(is_admin=True)
        )

@router.message(F.text == "🗑 Очистить базу")
async def menu_clear_db(message: Message, l10n):
    """Команда для очистки базы данных"""
    logger.info(f"Database cleanup requested by admin {message.from_user.id}")
    try:
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Да", callback_data="clear_db_confirm")
        kb.button(text="❌ Нет", callback_data="clear_db_cancel")
        kb.adjust(2)
        
        await message.answer(
            l10n.format_value("clear-db-confirm"),
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        logger.error(f"Error showing cleanup confirmation: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке команды",
            reply_markup=get_main_menu(is_admin=True)
        )

@router.callback_query(F.data == "clear_db_confirm")
async def clear_db_confirm(callback: CallbackQuery, session: AsyncSession, l10n):
    """Подтверждение очистки базы"""
    try:
        # Сначала отправляем сообщение об успехе
        await callback.message.edit_text(
            l10n.format_value("clear-db-success")
        )
        
        # Закрываем текущую сессию
        await session.close()
        
        # Создаем новый engine для закрытия всех соединений
        engine = create_async_engine(
            "sqlite+aiosqlite:///bot.db",
            echo=False
        )
        await engine.dispose()
        
        # Удаляем файл базы данных
        if os.path.exists("bot.db"):
            os.remove("bot.db")
            
        # Создаем новую пустую базу данных перед завершением
        new_engine = create_async_engine(
            "sqlite+aiosqlite:///bot.db",
            echo=False
        )
        async with new_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await new_engine.dispose()
            
        # Завершаем процесс
        os._exit(0)
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)
        await callback.message.edit_text(
            l10n.format_value("clear-db-error", {"error": str(e)})
        )

@router.callback_query(F.data == "clear_db_cancel")
async def clear_db_cancel(callback: CallbackQuery):
    """Отмена очистки базы"""
    await callback.message.delete()
