from typing import Callable, Dict, Any, Awaitable, List
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.filters import Command

from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, excluded_commands: List[str] = None):
        # Список команд-исключений по умолчанию
        self.excluded_commands = [
            '/donate', '/donat', '/донат',  # команды доната
            '/help'    # помощь
        ]
        
        # Добавляем пользовательские исключения, если они есть
        if excluded_commands:
            self.excluded_commands.extend(excluded_commands)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем команды из списка исключений
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lower()
            if command in self.excluded_commands:
                return await handler(event, data)

        # Для всех остальных команд проверяем подписку
        if not await IsSubscribedFilter()(event):
            await event.answer(
                "Для использования бота необходимо подписаться на наш канал:",
                reply_markup=get_subscription_keyboard()
            )
            return
        
        return await handler(event, data) 