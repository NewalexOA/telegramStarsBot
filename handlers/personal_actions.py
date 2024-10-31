from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _

from filters.chat_type import ChatTypeFilter
from keyboards.subscription import get_subscription_keyboard
from middlewares.check_subscription import check_subscription

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Этот хэндлер будет вызван, когда пользователь отправит команду /start
    """
    await message.answer(
        _("welcome"),
        reply_markup=await get_subscription_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Этот хэндлер будет вызван, когда пользователь отправит команду /help
    """
    await message.answer(_("help"))

@router.message(Command("language"))
async def cmd_language(message: Message):
    """
    Этот хэндлер будет вызван, когда пользователь отправит команду /language
    """
    await message.answer(
        _("language"),
        reply_markup=await get_subscription_keyboard()
    )

@router.callback_query(F.data == "check_subscription")
@check_subscription
async def check_subscription_callback(callback: CallbackQuery):
    """
    Этот хэндлер будет вызван, когда пользователь нажмет на кнопку проверки подписки
    """
    await callback.answer(_("subscription_checked"))





