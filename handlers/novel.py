from aiogram import Router, F
from aiogram.types import Message
from logs import get_logger
from filters.chat_type import ChatTypeFilter

logger = get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["private"]))
