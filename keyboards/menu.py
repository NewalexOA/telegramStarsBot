from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu(has_active_novel: bool = False, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Возвращает основное меню"""
    builder = ReplyKeyboardBuilder()
    
    # Добавляем базовые кнопки
    builder.add(KeyboardButton(text="🎮 Новелла"))
    
    # Добавляем кнопки для активной новеллы
    if has_active_novel:
        builder.add(KeyboardButton(text="📖 Продолжить"))
        builder.add(KeyboardButton(text="🔄 Рестарт"))
        
    # Добавляем стандартные кнопки
    builder.add(
        KeyboardButton(text="💝 Донат"),
        KeyboardButton(text="❓ Помощь")
    )
    builder.add(KeyboardButton(text="🔗 Реферальная ссылка"))
    
    # Добавляем админские кнопки
    if is_admin:
        builder.add(
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="🗑 Очистить базу")
        )
    
    # Настраиваем расположение кнопок в зависимости от количества кнопок
    buttons_list = list(builder.buttons)  # Преобразуем генератор в список
    total_buttons = len(buttons_list)
    
    if has_active_novel:
        if total_buttons <= 4:
            builder.adjust(2, 2)
        elif total_buttons <= 6:
            builder.adjust(2, 2, 2)
        else:
            builder.adjust(2, 2, 2, 2)
    else:
        if total_buttons <= 3:
            builder.adjust(1, 2)
        elif total_buttons <= 5:
            builder.adjust(1, 2, 2)
        else:
            builder.adjust(1, 2, 2, 2)
    
    return builder.as_markup(resize_keyboard=True) 