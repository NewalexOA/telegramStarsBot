from aiogram import Router
from aiogram.types import Message
from logs import get_logger
from filters.chat_type import ChatTypeFilter

logger = get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["group", "supergroup"]))

@router.message()
async def handle_group_message(message: Message):
    """
    Обработчик сообщений в группах
    """
    logger.info(
        "Processing group message",
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        event="group_message"
    )
