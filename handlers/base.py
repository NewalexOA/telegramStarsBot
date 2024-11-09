import structlog
from aiogram.types import Message
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard

logger = structlog.get_logger()

class PermissionMixin:
    """Миксин для проверки прав пользователя"""
    
    @staticmethod
    async def check_permissions(message: Message) -> tuple[bool, bool]:
        """Проверка прав пользователя"""
        is_admin = await IsAdminFilter(is_admin=True)(message)
        is_owner = await IsOwnerFilter(is_owner=True)(message)
        return is_admin, is_owner

    @staticmethod
    async def check_subscription(message: Message, l10n) -> bool:
        """Проверка подписки пользователя"""
        if not await IsSubscribedFilter()(message):
            await message.answer(
                l10n.format_value("subscription-required"),
                reply_markup=await get_subscription_keyboard(message),
                parse_mode="HTML"
            )
            return False
        return True 