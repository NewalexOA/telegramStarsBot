from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from filters.is_subscribed import IsSubscribedFilter

async def check_subscription_filter(event: Union[Message, CallbackQuery]) -> bool:
    """
    Фильтр для проверки подписки
    """
    return await IsSubscribedFilter()(event)

class CheckSubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки на канал
    """
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем подписку
        if not await check_subscription_filter(event):
            return
            
        # Если подписка есть, продолжаем обработку
        return await handler(event, data)
