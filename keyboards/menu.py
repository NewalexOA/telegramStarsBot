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
    
    # Настраиваем расположение кнопок
    if has_active_novel:
        builder.adjust(2, 2, 1, 1)  # Две кнопки в первых двух рядах, по одной в остальных
    else:
        builder.adjust(1, 2, 1)  # Одна кнопка в первом ряду, две во втором, одна в третьем
        
    if is_admin:
        builder.adjust(*([2] * (len(builder.buttons) // 2 + len(builder.buttons) % 2)))
    
    return builder.as_markup(resize_keyboard=True) 