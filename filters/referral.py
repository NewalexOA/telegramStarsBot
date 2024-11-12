from aiogram.filters import BaseFilter
from aiogram.types import Message
import structlog

logger = structlog.get_logger()

class ReferralCommandFilter(BaseFilter):
    """Filter for commands with referral code"""
    async def __call__(self, message: Message) -> bool:
        logger.info(
            "ReferralCommandFilter check",
            text=message.text,
            user_id=message.from_user.id,
            username=message.from_user.username
        )
        args = message.text.split()
        result = len(args) > 1 and args[1].startswith('ref_')
        logger.info(
            "ReferralCommandFilter result",
            result=result,
            args=args,
            user_id=message.from_user.id
        )
        return result

class RegularStartCommandFilter(BaseFilter):
    """Filter for regular start command without referral"""
    async def __call__(self, message: Message) -> bool:
        args = message.text.split()
        return len(args) == 1 