from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from logs import get_logger
from filters.chat_type import ChatTypeFilter
from filters.referral import ReferralCommandFilter
from utils.referral import get_user_ref_link, create_ref_link

logger = get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

@router.message(Command("ref"))
async def cmd_ref(message: Message, session: AsyncSession):
    """
    Получение реферальной ссылки
    """
    logger.info(
        "Processing ref command",
        user_id=message.from_user.id,
        event="referral_link_request"
    )
    ref_link = await get_user_ref_link(message.from_user.id)
    await message.answer(
        f"Ваша реферальная ссылка:\n{ref_link}\n\n"
        "Отправьте её друзьям и получайте бонусы!"
    )

@router.message(Command("start"), ReferralCommandFilter())
async def handle_referral_start(message: Message, command: Command, session: AsyncSession):
    """
    Обработка перехода по реферальной ссылке
    """
    logger.info(
        "Processing referral start",
        user_id=message.from_user.id,
        ref_code=command.args,
        event="referral_activation"
    )
    try:
        await create_ref_link(message.from_user.id, command.args, session)
        await message.answer("Реферальная ссылка активирована!")
    except Exception as e:
        logger.error(
            "Error activating referral",
            error=str(e),
            user_id=message.from_user.id,
            event="referral_activation_error"
        )
