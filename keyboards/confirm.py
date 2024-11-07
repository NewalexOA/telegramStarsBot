from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

class ConfirmKeyboardData:
    """Данные для кнопок подтверждения"""
    CONFIRM = {
        'text': "✅ Да",
        'callback': "confirm"
    }
    CANCEL = {
        'text': "❌ Нет",
        'callback': "cancel"
    }

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру подтверждения
    :param action: действие для подтверждения (например, 'clear_db', 'restart')
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text=ConfirmKeyboardData.CONFIRM['text'],
        callback_data=f"{action}_{ConfirmKeyboardData.CONFIRM['callback']}"
    )
    kb.button(
        text=ConfirmKeyboardData.CANCEL['text'],
        callback_data=f"{action}_{ConfirmKeyboardData.CANCEL['callback']}"
    )
    kb.adjust(2)
    return kb.as_markup()
