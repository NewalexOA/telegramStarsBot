from typing import Union
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from config_reader import get_config, BotConfig
from logs import get_logger

logger = get_logger()
bot_config = get_config(BotConfig, "bot")

class IsOwnerFilter(BaseFilter):
    """
    Filter that checks if user is bot owner
    """
    def __init__(self, is_owner: bool) -> None:
        self.is_owner = is_owner

    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        user_id = obj.from_user.id
        
        # Получаем список владельцев из конфига
        owners = bot_config.owners
        is_owner = user_id in owners
        
        # Логируем проверку прав владельца
        logger.info(
            "Checking owner rights",
            user_id=user_id,
            is_owner=is_owner,
            filter_result=is_owner == self.is_owner,
            check_type="owner_check"
        )
        
        return is_owner == self.is_owner
