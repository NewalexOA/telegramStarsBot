from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📚 Подписаться на канал",
        url="https://t.me/+_lWXgZC_XNMwYWRi"
    )
    kb.button(
        text="🔄 Проверить подписку",
        callback_data="check_subscription"
    )
    kb.adjust(1)
    return kb.as_markup() 