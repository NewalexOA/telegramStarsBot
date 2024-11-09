from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import get_config, BotConfig
import structlog

logger = structlog.get_logger()

class IsOwnerFilter(BaseFilter):
    """
    Filter that checks if user is bot owner
    """
    def __init__(self, is_owner: bool) -> None:
        self.is_owner = is_owner
        self.bot_config = get_config(BotConfig, "bot")

    async def __call__(self, message: Message) -> bool:
        try:
            user_id = message.from_user.id
            is_owner = user_id in self.bot_config.owners
            logger.debug(
                "Checking owner rights",
                user_id=user_id,
                owners=self.bot_config.owners,
                is_owner=is_owner,
                expected=self.is_owner
            )
            return is_owner == self.is_owner
        except Exception as e:
            logger.error(f"Error in IsOwnerFilter: {e}")
            return False
