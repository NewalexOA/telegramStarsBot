from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import structlog
from handlers.novel import PRIORITIES  # Исправляем импорт

from models.referral import Referral, ReferralLink, PendingReferral
from filters.chat_type import ChatTypeFilter
from filters.referral import ReferralCommandFilter

router = Router()
router.message.filter(ChatTypeFilter(["private"]))
logger = structlog.get_logger()

@router.message(
    Command("start"),
    ReferralCommandFilter(),
    flags={"priority": PRIORITIES["COMMAND"] + 1}  # Приоритет выше обычного /start
)
async def cmd_start_with_ref(message: Message, session: AsyncSession, l10n):
    """Обработка реферальных команд /start ref_code"""
    logger.info(
        "cmd_start_with_ref called",
        text=message.text,
        user_id=message.from_user.id,
        username=message.from_user.username
    )
    try:
        args = message.text.split()
        ref_code = args[1][4:]  # Убираем префикс 'ref_'
        
        logger.info(
            "Processing referral start command",
            user_id=message.from_user.id,
            ref_code=ref_code
        )
        
        async with session.begin():
            # Проверяем существование реферальной ссылки
            ref_link = await session.scalar(
                select(ReferralLink).where(ReferralLink.code == ref_code)
            )
            
            if not ref_link or ref_link.user_id == message.from_user.id:
                await logger.ainfo(
                    "Invalid referral link or self-referral",
                    ref_code=ref_code,
                    user_id=message.from_user.id
                )
                raise ValueError("Invalid referral")
            
            # Проверяем, не был ли уже приглашен
            existing = await session.scalar(
                select(Referral).where(Referral.referred_id == message.from_user.id)
            )
            if existing:
                await logger.ainfo(
                    "User already referred",
                    user_id=message.from_user.id
                )
                raise ValueError("Already referred")
            
            # Удаляем старые pending referrals
            await session.execute(
                delete(PendingReferral).where(
                    PendingReferral.user_id == message.from_user.id
                )
            )
            
            # Создаем новый pending referral
            pending = PendingReferral(
                user_id=message.from_user.id,
                ref_code=ref_code
            )
            session.add(pending)
            
            logger.info(
                "Created pending referral",
                user_id=message.from_user.id,
                ref_code=ref_code
            )
            
            await logger.ainfo(
                "Saved pending referral",
                ref_code=ref_code,
                user_id=message.from_user.id,
                username=message.from_user.username
            )
            
    except ValueError:
        # Ожидаемые ошибки (невалидная ссылка, уже приглашен)
        pass
    except Exception as e:
        await logger.aerror(
            "Error processing referral",
            error=str(e),
            user_id=message.from_user.id,
            ref_code=ref_code
        )
    finally:
        # Вместо самостоятельной отправки сообщения вызываем обработчик обычного /start
        from handlers.personal_actions import cmd_start
        await cmd_start(message, session, l10n)
