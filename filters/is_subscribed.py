import structlog
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember
from typing import Union

from config_reader import BotConfig, get_config

logger = structlog.get_logger()

class IsSubscribedFilter(BaseFilter):
    def __init__(self) -> None:
        # Получаем конфиг при инициализации фильтра
        self.bot_config = get_config(BotConfig, "bot")  # Исправлен вызов функции

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        # Получаем бота из контекста события
        bot = event.bot
        
        # Получаем ID пользователя
        user_id = event.from_user.id
        
        # Логируем начало проверки
        await logger.ainfo(
            "Starting subscription check",
            channel_id=self.bot_config.required_channel_id,
            user_id=user_id,
            username=event.from_user.username
        )
        
        try:
            # Получаем информацию о чате
            chat = await bot.get_chat(self.bot_config.required_channel_id)
            await logger.ainfo(
                "Got chat info",
                chat_id=chat.id,
                chat_title=chat.title,
                chat_type=chat.type,
                chat_username=chat.username
            )
            
            # Получаем статус участника
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
            
            # Проверяем, является ли пользователь подписчиком
            is_member = isinstance(member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember))
            
            # Логируем результат проверки
            await logger.ainfo(
                "Subscription check completed",
                is_subscribed=is_member,
                status=member.status,
                user_id=user_id,
                username=event.from_user.username
            )
            
            return is_member
            
        except Exception as e:
            # Логируем ошибку
            await logger.aerror(
                "Error checking subscription",
                error=str(e),
                user_id=user_id,
                username=event.from_user.username
            )
            return False