from aiogram.filters import BaseFilter
from aiogram.types import Message
import structlog

logger = structlog.get_logger()

class ReferralCommandFilter(BaseFilter):
    """Filter for commands with referral code"""
    async def __call__(self, message: Message) -> bool:
        args = message.text.split()
        result = len(args) > 1 and args[1].startswith('ref_')
        await logger.adebug(
            "ReferralCommandFilter check",
            text=message.text,
            args=args,
            result=result,
            user_id=message.from_user.id,
            username=message.from_user.username
        )
        return result

class RegularStartCommandFilter(BaseFilter):
    """Filter for regular start command without referral"""
    async def __call__(self, message: Message) -> bool:
        args = message.text.split()
        return len(args) == 1 