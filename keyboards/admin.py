from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup
import structlog

logger = structlog.get_logger()

def get_admin_menu(has_active_novel: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура для администратора"""
    builder = ReplyKeyboardBuilder()
    
    logger.debug(f"Building admin keyboard, has_active_novel: {has_active_novel}")
    
    # Основные кнопки
    builder.button(text="🎮 Новелла")
    if has_active_novel:
        builder.button(text="📖 Продолжить")
        builder.button(text="🔄 Рестарт")
    
    # Админские кнопки
    builder.button(text="📊 Статистика")
    builder.button(text="🗑 Очистить базу")
    
    # Общие кнопки
    builder.button(text="🔗 Реферальная ссылка")
    builder.button(text="💝 Донат")
    builder.button(text="❓ Помощь")
    
    # Настраиваем расположение кнопок
    if has_active_novel:
        builder.adjust(2, 2, 2, 2)  # 8 кнопок: 2-2-2-2
    else:
        builder.adjust(2, 2, 2, 1)  # 7 кнопок: 2-2-2-1
    
    keyboard = builder.as_markup(resize_keyboard=True)
    logger.debug("Admin keyboard built successfully")
    return keyboard 