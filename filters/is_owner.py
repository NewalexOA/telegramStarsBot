from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config_reader import BotConfig, get_config

class IsOwnerFilter(BaseFilter):
    def __init__(self, is_owner: bool) -> None:
        self.is_owner = is_owner

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        bot_config = get_config(BotConfig, "bot")
        
        user_id = event.from_user.id
        is_owner = user_id in bot_config.owners
        
        return is_owner == self.is_owner
