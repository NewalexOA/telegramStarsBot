from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_reader import get_config, BotConfig

async def get_subscription_keyboard(message, is_subscribed: bool = False) -> InlineKeyboardMarkup:
    """Get subscription keyboard based on subscription status"""
    bot_config = get_config(BotConfig, "bot")
    kb = InlineKeyboardBuilder()
    
    if not is_subscribed:
        # Кнопки для неподписанных пользователей
        kb.button(
            text="📚 Подписаться на канал",
            url=bot_config.required_channel_invite
        )
        kb.button(
            text="🔄 Проверить подписку",
            callback_data="check_subscription"
        )
    else:
        # Кнопка для подписанных пользователей
        kb.button(
            text="🎮 Запустить новеллу",
            callback_data="start_novel"
        )
    
    kb.adjust(1)  # Кнопки в столбик
    return kb.as_markup() 