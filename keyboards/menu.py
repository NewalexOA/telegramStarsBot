from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(has_active_novel: bool = False, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Создает основное меню бота
    
    Args:
        has_active_novel (bool): Есть ли активная новелла у пользователя
        is_admin (bool): Является ли пользователь админом/владельцем
    """
    builder = ReplyKeyboardBuilder()
    
    # Основные кнопки
    builder.button(text="🎮 Новелла")
    if has_active_novel:
        builder.button(text="📖 Продолжить")
        builder.button(text="🔄 Рестарт")
    
    # Админские кнопки
    if is_admin:
        builder.button(text="📊 Статистика")
        builder.button(text="🗑 Очистить базу")
    
    # Общие кнопки
    builder.button(text="🔗 Реферальная ссылка")
    builder.button(text="💝 Донат")
    builder.button(text="❓ Помощь")
    
    # Размещаем кнопки в зависимости от количества
    if is_admin:
        if has_active_novel:
            builder.adjust(2, 2, 2, 1)  # 7 кнопок: 2-2-2-1
        else:
            builder.adjust(2, 2, 2)  # 6 кнопок: 2-2-2
    else:
        if has_active_novel:
            builder.adjust(2, 2, 2)  # 6 кнопок: 2-2-2
        else:
            builder.adjust(2, 2)  # 4 кнопки: 2-2
    
    return builder.as_markup(
        resize_keyboard=True,
        persistent=True
    ) 