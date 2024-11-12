from aiogram.filters import BaseFilter
from aiogram.types import Message
from config_reader import bot_config

class IsAdminFilter(BaseFilter):
    """Filter that checks if user is admin"""
    def __init__(self, is_admin: bool) -> None:
        self.is_admin = is_admin

    async def __call__(self, message: Message) -> bool:
        # Проверяем, является ли пользователь владельцем бота
        is_admin = message.from_user.id in bot_config.owners
        return is_admin == self.is_admin
