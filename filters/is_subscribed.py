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
            # Логируем начало проверки
            await self.logger.ainfo(
                "Starting subscription check",
                user_id=message.from_user.id,
                username=message.from_user.username,
                channel_id=self.channel_id
            )
            
            # Получаем информацию о чате
            chat = await message.bot.get_chat(chat_id=self.channel_id)
            await self.logger.ainfo(
                "Got chat info",
                chat_id=chat.id,
                chat_type=chat.type,
                chat_title=chat.title,
                chat_username=chat.username
            )
            
            # Получаем информацию о боте в чате
            bot_member = await message.bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=message.bot.id
            )
            await self.logger.ainfo(
                "Got bot member info",
                bot_id=message.bot.id,
                bot_status=bot_member.status,
                can_manage_chat=getattr(bot_member, "can_manage_chat", False)
            )
            
            # Получаем статус участника
            member = await message.bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=message.from_user.id
            )
            
            # Подробно логируем статус
            await self.logger.ainfo(
                "Got member status",
                user_id=message.from_user.id,
                username=message.from_user.username,
                status=member.status,
                raw_status=str(member.status),
                raw_data=member.model_dump()
            )

            # Проверяем статус
            result = member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR
            ]
            
            # Логируем результат
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
                channel_id=self.channel_id,
                error_details=e.__dict__
            )
            return False
        except Exception as e:
            await self.logger.aerror(
                "Unexpected error while checking subscription",
                user_id=message.from_user.id,
                username=message.from_user.username,
                error=str(e),
                error_type=type(e).__name__,
                channel_id=self.channel_id,
                error_details=e.__dict__
            )
            return False