from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from keyboards.subscription import get_subscription_keyboard
from middlewares.check_subscription import check_subscription

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(message: Message, l10n):
    """
    Этот хэндлер будет вызван только для обычной команды /start без реферального кода
    """
    await message.answer(
        l10n.format_value("hello-msg"),
        reply_markup=await get_subscription_keyboard(message),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message, l10n):
    """
    Этот хэндлер будет вызван, когда пользователь отправит команду /help
    """
    await message.answer(
        l10n.format_value("help"),
        parse_mode="HTML"
    )

@router.message(Command("language"))
async def cmd_language(message: Message, l10n):
    """
    Этот хэндлер будет вызван, когда пользователь отправит команду /language
    """
    await message.answer(
        l10n.format_value("language"),
        reply_markup=await get_subscription_keyboard(message),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "check_subscription")
@check_subscription
async def check_subscription_callback(callback: CallbackQuery, l10n):
    """
    Этот хэндлер будет вызван, когда пользователь нажмет на кнопку проверки подписки
    """
    await callback.answer(l10n.format_value("subscription_checked"))

@router.callback_query(F.data == "show_donate")
async def show_donate_info(callback: CallbackQuery, l10n):
    """Показываем информацию о донате"""
    await callback.message.answer(l10n.format_value("donate-input-error"))
    await callback.answer()

@router.callback_query(F.data == "start_novel")
async def start_novel(callback: CallbackQuery, l10n):
    """Начинаем новеллу"""
    # Здесь будет логика запуска новеллы
    await callback.message.answer("Запуск новеллы... (в разработке)")
    await callback.answer()
