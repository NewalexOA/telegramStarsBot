from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_reader import get_config, BotConfig
from filters.is_subscribed import IsSubscribedFilter

async def get_subscription_keyboard(message) -> InlineKeyboardMarkup:
    """Get subscription keyboard based on subscription status"""
    is_subscribed = await IsSubscribedFilter()(message)
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
        # Кнопки для подписанных пользователей
        kb.button(
            text="🎮 Запустить новеллу",
            callback_data="start_novel"
        )
        kb.button(
            text="💝 Донат автору",
            callback_data="show_donate"
        )
    
    kb.adjust(1)  # Кнопки в столбик
    return kb.as_markup() 