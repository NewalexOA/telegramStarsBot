import structlog
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard

logger = structlog.get_logger()

class CheckSubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки подписки на канал"""
    
    def __init__(self):
        """Инициализация middleware"""
        self.excluded_commands = {"/start", "/help", "/language"}

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Пропускаем исключенные команды
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lower()
            if command in self.excluded_commands:
                return await handler(event, data)

        is_subscribed = await IsSubscribedFilter()(event)
        
        if is_subscribed:
            return await handler(event, data)
        else:
            # Отправляем сообщение о необходимости подписки
            l10n = data.get('l10n')
            if isinstance(event, Message):
                await event.answer(
                    l10n.format_value("subscription-check-failed"),
                    reply_markup=await get_subscription_keyboard(event),
                    parse_mode="HTML"
                )
            else:
                await event.answer(
                    l10n.format_value("subscription-check-failed"),
                    show_alert=True
                )
            return
