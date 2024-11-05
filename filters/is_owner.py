from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import get_config, BotConfig

bot_config = get_config(BotConfig, "bot")

class IsOwnerFilter(BaseFilter):
    """
    Filter that checks if user is bot owner
    """
    def __init__(self, is_owner: bool) -> None:
        self.is_owner = is_owner

    async def __call__(self, message: Message) -> bool:
        is_owner = message.from_user.id in bot_config.owners
        return is_owner == self.is_owner
