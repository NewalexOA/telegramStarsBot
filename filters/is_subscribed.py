from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import structlog
from config_reader import get_config, BotConfig

class IsSubscribedFilter(BaseFilter):
    """
    Filter that checks if user is subscribed to required channel
    """
    def __init__(self):
        self.logger = structlog.get_logger()
        bot_config: BotConfig = get_config(model=BotConfig, root_key="bot")
        self.channel_id = bot_config.required_channel_id

    async def __call__(self, message: Message) -> bool:
        try:
            await self.logger.ainfo(
                "Starting subscription check",
                user_id=message.from_user.id,
                username=message.from_user.username,
                channel_id=self.channel_id
            )
            
            member = await message.bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=message.from_user.id
            )
            
            await self.logger.ainfo(
                "Got member status",
                user_id=message.from_user.id,
                username=message.from_user.username,
                status=member.status,
                raw_status=str(member.status)
            )

            result = member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR
            ]
            
            await self.logger.ainfo(
                "Subscription check completed",
                user_id=message.from_user.id,
                username=message.from_user.username,
                is_subscribed=result,
                status=member.status
            )
            
            return result

        except TelegramBadRequest as e:
            await self.logger.aerror(
                "Telegram error while checking subscription",
                user_id=message.from_user.id,
                username=message.from_user.username,
                error=str(e),
                error_type=type(e).__name__,
                channel_id=self.channel_id
            )
            return False
        except Exception as e:
            await self.logger.aerror(
                "Unexpected error while checking subscription",
                user_id=message.from_user.id,
                username=message.from_user.username,
                error=str(e),
                error_type=type(e).__name__,
                channel_id=self.channel_id
            )
            return False 