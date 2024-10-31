from aiogram.filters import BaseFilter
from aiogram.types import Message
import structlog

from config_reader import get_config, BotConfig

class IsOwnerFilter(BaseFilter):
    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def __call__(self, message: Message) -> bool:
        bot_config: BotConfig = get_config(model=BotConfig, root_key="bot")
        is_owner = message.from_user.id in bot_config.owners
        logger = structlog.get_logger()
        await logger.ainfo(
            "Owner check", 
            user_id=message.from_user.id, 
            is_owner=is_owner,
            owners_list=bot_config.owners
        )
        return is_owner
