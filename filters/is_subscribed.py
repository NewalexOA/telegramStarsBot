import structlog
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union

from config_reader import BotConfig, get_config

logger = structlog.get_logger()

class IsSubscribedFilter(BaseFilter):
    def __init__(self) -> None:
        self.bot_config = get_config(BotConfig, "bot")

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        bot = event.bot
        user_id = event.from_user.id
        
        await logger.ainfo(
            "Starting subscription check",
            channel_id=self.bot_config.required_channel_id,
            user_id=user_id,
            username=event.from_user.username
        )
        
        try:
            # Сразу пробуем получить статус участника
            member = await bot.get_chat_member(
                chat_id=self.bot_config.required_channel_id,
                user_id=user_id
            )
            
            # Логируем полученный статус
            await logger.ainfo(
                "Got member status",
                raw_status=member.status,
                status=member.status,
                user_id=user_id,
                username=event.from_user.username
            )
            
            # Проверяем статус
            is_member = member.status in ['creator', 'administrator', 'member']
            
            await logger.ainfo(
                "Subscription check completed",
                is_subscribed=is_member,
                status=member.status,
                user_id=user_id,
                username=event.from_user.username
            )
            
            return is_member
            
        except Exception as e:
            await logger.aerror(
                "Error checking subscription",
                error=str(e),
                user_id=user_id,
                username=event.from_user.username
            )
            return False
