from typing import Callable, Dict, Any, Awaitable, List
from functools import wraps
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
import structlog

from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard
from models.referral import PendingReferral
from utils.referral_processor import process_referral

logger = structlog.get_logger()

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, excluded_commands: List[str] = None):
        self.excluded_commands = [
            '/donate', '/donat', '/донат',
            '/help',
            '/start'
        ]
        if excluded_commands:
            self.excluded_commands.extend(excluded_commands)

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.text:
            command = event.text.split()[0].lower()
            if command in self.excluded_commands:
                return await handler(event, data)

        user_id = event.from_user.id
        
        is_subscribed = await IsSubscribedFilter()(event)
        
        if is_subscribed:
            session = data.get('session')
            if session:
                result = await session.execute(
                    select(PendingReferral)
                    .where(PendingReferral.user_id == user_id)
                    .order_by(PendingReferral.created_at.desc())
                )
                pending = result.scalar_one_or_none()
                
                if pending:
                    await logger.ainfo(
                        "Processing pending referral",
                        ref_code=pending.ref_code,
                        user_id=user_id
                    )
                    message = event.message if isinstance(event, CallbackQuery) else event
                    await process_referral(session, pending.ref_code, user_id, message)
                    await session.delete(pending)
                    await session.commit()
            
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
            result = await session.execute(
                select(PendingReferral)
                .where(PendingReferral.user_id == event.from_user.id)
                .order_by(PendingReferral.created_at.desc())
            )
            pending = result.scalar_one_or_none()
            
            if pending:
                await logger.ainfo(
                    "Processing pending referral",
                    ref_code=pending.ref_code,
                    user_id=event.from_user.id
                )
                await process_referral(session, pending.ref_code, event.from_user.id, event.message)
                await session.delete(pending)
                await session.commit()
        
        return await func(event, *args, **kwargs)
    return wrapper
