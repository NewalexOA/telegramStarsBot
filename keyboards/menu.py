from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(has_active_novel: bool = False) -> ReplyKeyboardMarkup:
    """
    Создает основное меню бота
    
    Args:
        has_active_novel (bool): Есть ли активная новелла у пользователя
    """
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🎮 Новелла")
    if has_active_novel:
        builder.button(text="📖 Продолжить")
        builder.button(text="🔄 Рестарт")
    builder.button(text="💝 Донат")
    builder.button(text="❓ Помощь")
    
    # Размещаем кнопки в зависимости от количества
    if has_active_novel:
        builder.adjust(2, 2, 1)  # 5 кнопок: 2-2-1
    else:
        builder.adjust(2, 1)  # 3 кнопки: 2-1
    
    return builder.as_markup(
        resize_keyboard=True,
        persistent=True
    ) 