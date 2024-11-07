from typing import Union
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from config_reader import get_config, BotConfig
from logs import get_logger

logger = get_logger()
bot_config = get_config(BotConfig, "bot")

class IsAdminFilter(BaseFilter):
    def __init__(self, is_admin: bool) -> None:
        self.is_admin = is_admin

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        user_id = obj.from_user.id
        
        # Получаем список админов из конфига
        admins = bot_config.owners
        is_admin = user_id in admins
        
        # Логируем проверку прав администратора
        logger.info(
            "Checking admin rights",
            user_id=user_id,
            is_admin=is_admin,
            filter_result=is_admin == self.is_admin,
            check_type="admin_check"
        )
        
        return is_admin == self.is_admin
