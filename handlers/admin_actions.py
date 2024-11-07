from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from logs import get_logger
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from services.novel import NovelService
from utils.db import clear_database

logger = get_logger()

# Создаем роутер
router = Router()
router.message.filter(IsAdminFilter(is_admin=True))

@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """
    Проверка работоспособности бота
    Доступно только администраторам
    """
    logger.info(
        "Processing ping command",
        user_id=message.from_user.id,
        event="admin_ping"
    )
    await message.answer("Pong!")

@router.message(F.text == "📊 Статистика")
async def stats_button(message: Message, session: AsyncSession):
    """
    Кнопка получения статистики
    Доступно только администраторам
    """
    logger.info(
        "Processing stats button",
        user_id=message.from_user.id,
        event="admin_stats_button"
    )
    try:
        novel_service = NovelService(session)
        stats = await novel_service.get_stats()
        
        # Форматируем статистику
        stats_text = "📊 Статистика:\n"
        if "total_novels" in stats:
            stats_text += f"Всего новелл: {stats['total_novels']}\n"
        if "completed_novels" in stats:
            stats_text += f"Завершенных: {stats['completed_novels']}\n"
        if "active_novels" in stats:
            stats_text += f"Активных: {stats['active_novels']}\n"
        if "total_messages" in stats:
            stats_text += f"Всего сообщений: {stats['total_messages']}"
            
        await message.answer(stats_text)
        
        logger.info(
            "Stats displayed successfully",
            user_id=message.from_user.id,
            stats=stats,
            event="admin_stats_success"
        )
    except Exception as e:
        logger.error(
            "Error getting stats",
            error=str(e),
            user_id=message.from_user.id,
            event="admin_stats_error"
        )
        await message.answer("Ошибка при получении статистики")

@router.message(F.text == "🗑 Очистить базу")
async def clear_db_button(message: Message):
    """
    Кнопка очистки базы данных
    Доступно только владельцам
    """
    logger.info(
        "Processing clear DB button",
        user_id=message.from_user.id,
        event="admin_clear_db_request"
    )
    if not await IsOwnerFilter(is_owner=True)(message):
        logger.warning(
            "Unauthorized clear DB attempt",
            user_id=message.from_user.id,
            event="admin_clear_db_unauthorized"
        )
        await message.answer("У вас нет прав для очистки базы данных")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="clear_db_confirm")
    kb.button(text="❌ Нет", callback_data="clear_db_cancel")
    await message.answer(
        "⚠️ Вы уверены, что хотите очистить базу данных?\n"
        "Все данные будут удалены безвозвратно!",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "clear_db_confirm")
async def clear_db_confirm(callback: CallbackQuery, session: AsyncSession):
    """
    Подтверждение очистки базы данных
    """
    user_id = callback.from_user.id
    logger.info(
        "Processing clear DB confirmation",
        user_id=user_id,
        event="admin_clear_db_confirm"
    )
    
    # Проверяем права владельца повторно
    if not await IsOwnerFilter(is_owner=True)(callback.message):
        logger.warning(
            "Unauthorized clear DB confirmation attempt",
            user_id=user_id,
            event="admin_clear_db_unauthorized"
        )
        await callback.message.edit_text("У вас нет прав для очистки базы данных")
        return
        
    try:
        # Информируем о начале процесса
        await callback.message.edit_text("Начинаем очистку базы данных...")
        
        # Очищаем базу
        await clear_database(session)
        
        # Информируем об успешном завершении
        await callback.message.edit_text(
            "База данных успешно очищена!\n"
            "Рекомендуется перезапустить бота."
        )
        
        logger.info(
            "Database cleared successfully",
            user_id=user_id,
            event="admin_clear_db_success"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "Error clearing database",
            error=error_msg,
            user_id=user_id,
            event="admin_clear_db_error"
        )
        await callback.message.edit_text(
            f"Ошибка при очистке базы данных:\n{error_msg}\n"
            "Проверьте логи для получения дополнительной информации."
        )

@router.callback_query(F.data == "clear_db_cancel")
async def clear_db_cancel(callback: CallbackQuery):
    """
    Отмена очистки базы данных
    """
    logger.info(
        "Clear DB cancelled",
        user_id=callback.from_user.id,
        event="admin_clear_db_cancel"
    )
    await callback.message.edit_text("Очистка базы данных отменена")
