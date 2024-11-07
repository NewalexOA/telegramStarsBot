from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import get_config, BotConfig
import structlog

logger = structlog.get_logger()

class IsSubscribedFilter(BaseFilter):
    def __init__(self) -> None:
        self.bot_config = get_config(BotConfig, "bot")

    async def __call__(self, message: Message) -> bool:
        logger.info(
            "Checking channel subscription",
            extra={
                "user_id": message.from_user.id,
                "channel_id": self.bot_config.required_channel_id,
                "check_type": "subscription_check_start"
            }
        )
        try:
            member = await message.bot.get_chat_member(
                self.bot_config.required_channel_id,
                message.from_user.id
            )
            result = member.status not in ["left", "kicked", "banned"]
            logger.info(
                "Subscription check result",
                extra={
                    "user_id": message.from_user.id,
                    "is_subscribed": result,
                    "check_type": "subscription_check_complete"
                }
            )
            return result
        except Exception as e:
            logger.error(
                "Error checking subscription",
                extra={
                    "user_id": message.from_user.id,
                    "error": str(e),
                    "check_type": "subscription_check_error"
                }
            )
            return False
