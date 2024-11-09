import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.is_admin import IsAdminFilter
from services.admin import AdminService

logger = structlog.get_logger()

router = Router(name="admin")
router.message.filter(IsAdminFilter(is_admin=True))
router.callback_query.filter(IsAdminFilter(is_admin=True))

@router.message(Command("stats"))
async def cmd_stats(
    message: Message,
    admin_service: AdminService,
    l10n
):
    """Получение статистики бота"""
    try:
        stats = await admin_service.get_stats()
        
        stats_text = (
            f"📊 Статистика бота:\n\n"
            f"👥 Всего пользователей: {stats['total_users']}\n"
            f"📚 Активных новелл: {stats['active_novels']}\n"
            f"✅ Завершенных новелл: {stats['completed_novels']}"
        )
        
        await message.answer(stats_text)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        await message.answer(l10n.format_value("error-getting-stats"))

@router.message(F.text == "🗑 Очистить базу")
async def menu_clear_db(
    message: Message,
    admin_service: AdminService,
    l10n
):
    """Обработчик кнопки очистки базы"""
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
        logger.error(f"Error preparing clear DB: {e}", exc_info=True)
        await message.answer(l10n.format_value("error-clearing-db"))

@router.callback_query(F.data == "clear_db_confirm")
async def clear_db_confirm(
    callback: CallbackQuery,
    admin_service: AdminService,
    l10n
):
    """Подтверждение очистки базы"""
    try:
        await admin_service.clear_database()
        await callback.message.edit_text(l10n.format_value("db-cleared"))
        logger.info("Database cleared by admin", admin_id=callback.from_user.id)
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}", exc_info=True)
        await callback.message.edit_text(l10n.format_value("error-clearing-db"))

@router.callback_query(F.data == "clear_db_cancel")
async def clear_db_cancel(callback: CallbackQuery, l10n):
    """Отмена очистки базы"""
    await callback.message.edit_text(l10n.format_value("db-clear-cancelled"))
