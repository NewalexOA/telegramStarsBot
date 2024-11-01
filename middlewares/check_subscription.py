from typing import Callable, Dict, Any, Awaitable, List
from functools import wraps
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
import structlog

from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard
from models.referral import PendingReferral
from handlers.referral import process_referral

logger = structlog.get_logger()

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, excluded_commands: List[str] = None):
        self.excluded_commands = [
            '/donate', '/donat', '/донат', '/donate@Novel_story_game_dev_bot',
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
        # Для сообщений проверяем исключенные команды
        if isinstance(event, Message) and event.text:
            # Разбиваем текст на части и берем первое слово
            parts = event.text.split()
            if not parts:
                return await handler(event, data)
            
            # Извлекаем команду (первое слово до пробела или целиком, если пробелов нет)
            command = parts[0].split('@')[0].lower()  # Также убираем @bot_username если есть
            
            if command in self.excluded_commands:
                return await handler(event, data)

        # Получаем user_id в зависимости от типа события
        user_id = event.from_user.id
        
        is_subscribed = await IsSubscribedFilter()(event)
        
        # Проверяем реферала при первой подписке
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
                        "Processing pending referral on first subscription",
                        ref_code=pending.ref_code,
                        user_id=user_id
                    )
                    # Для callback используем event.message
                    message = event.message if isinstance(event, CallbackQuery) else event
                    await process_referral(session, pending.ref_code, user_id, message)
                    await session.delete(pending)
                    await session.commit()
            
            return await handler(event, data)
        else:
            # Отправляем разные ответы для Message и CallbackQuery
            if isinstance(event, Message):
                await event.answer(
                    "Для использования бота необходимо подписаться на наш канал:",
                    reply_markup=await get_subscription_keyboard(event),
                    parse_mode="HTML"
                )
            else:
                await event.answer(
                    "Для использования бота необходимо подписаться на наш канал",
                    show_alert=True
                )
            return
        
        return await handler(event, data)

def check_subscription(func: Callable) -> Callable:
    """Декоратор для проверки подписки"""
    @wraps(func)
    async def wrapper(event: CallbackQuery, *args, **kwargs):
        if not await IsSubscribedFilter()(event):
            await event.answer(
                "Для использования бота необходимо подписаться на наш канал",
                show_alert=True
            )
            return
            
        # Проверяем наличие отложенного реферала
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
