from typing import Callable, Dict, Any, Awaitable, List
from functools import wraps
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import structlog

from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard
from utils.referral_processor import process_pending_referral

logger = structlog.get_logger()

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, excluded_commands: List[str] = None):
        self.excluded_commands = [
            '/donate', '/donat', '/донат',
            '/help',
            '/start',
            '📊 Статистика',
            '🗑 Очистить базу'
        ]
        if excluded_commands:
            self.excluded_commands.extend(excluded_commands)

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        logger.info(
            "Check subscription middleware called",
            user_id=event.from_user.id,
            text=event.text if isinstance(event, Message) else None
        )
        
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lower()
            if command in self.excluded_commands:
                logger.info(
                    "Command excluded from subscription check",
                    command=command
                )
                return await handler(event, data)
        
        is_subscribed = await IsSubscribedFilter()(event)
        logger.info(
            "Subscription check result",
            user_id=event.from_user.id,
            is_subscribed=is_subscribed
        )
        
        if is_subscribed:
            session = data.get('session')
            if session:
                try:
                    await process_pending_referral(
                        event.from_user.id,
                        session,
                        event
                    )
                except Exception as e:
                    logger.error(
                        "Error processing pending referral in middleware",
                        error=str(e),
                        user_id=event.from_user.id
                    )
            return await handler(event, data)
        else:
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

def check_subscription(func: Callable) -> Callable:
    """Декоратор для проверки подписки"""
    @wraps(func)
    async def wrapper(event: CallbackQuery, *args, **kwargs):
        l10n = kwargs.get('l10n')
        if not await IsSubscribedFilter()(event):
            await event.answer(
                l10n.format_value("subscription-check-failed"),
                show_alert=True
            )
            return
            
        session = kwargs.get('session')
        if session:
            try:
                await process_pending_referral(
                    event.from_user.id,
                    session,
                    event
                )
            except Exception as e:
                logger.error(
                    "Error processing pending referral in decorator",
                    error=str(e),
                    user_id=event.from_user.id
                )
        
        return await func(event, *args, **kwargs)
    return wrapper
