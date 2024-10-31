from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_reader import get_config, BotConfig

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    bot_config: BotConfig = get_config(model=BotConfig, root_key="bot")
    
    kb = InlineKeyboardBuilder()
    kb.button(
        text="📚 Подписаться на канал",
        url=bot_config.required_channel_invite
    )
    kb.button(
        text="🔄 Проверить подписку",
        callback_data="check_subscription"
    )
    kb.adjust(1)
    return kb.as_markup() 