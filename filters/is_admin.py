from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import get_config, BotConfig
import structlog

logger = structlog.get_logger()

class IsAdminFilter(BaseFilter):
    """
    Filter that checks if user is admin
    """
    def __init__(self, is_admin: bool) -> None:
        self.is_admin = is_admin
        self.bot_config = get_config(BotConfig, "bot")

    async def __call__(self, message: Message) -> bool:
        try:
            user_id = message.from_user.id
            # Проверяем значение owners из конфига
            owners = self.bot_config.owners
            logger.debug(
                "Checking admin rights",
                user_id=user_id,
                owners=owners,
                is_admin=user_id in owners,
                expected=self.is_admin
            )
            
            # Проверяем, является ли пользователь владельцем бота
            is_user_admin = user_id in owners
            
            # Возвращаем True если статус админа совпадает с ожидаемым
            result = is_user_admin == self.is_admin
            logger.debug(
                "Admin check completed",
                user_id=user_id,
                result=result,
                expected=self.is_admin
            )
            return result
            
        except Exception as e:
            logger.error(
                "Error in IsAdminFilter",
                error=str(e),
                user_id=message.from_user.id
            )
            return False
