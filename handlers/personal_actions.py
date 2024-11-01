import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluent.runtime import FluentLocalization
from keyboards.subscription import get_subscription_keyboard
from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from middlewares.check_subscription import check_subscription

# Declare router
router = Router()
router.message.filter(ChatTypeFilter(["private"]))

# Declare logger
logger = structlog.get_logger()

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

@router.message(Command("donate", "donat", "донат"))
async def cmd_donate(message: Message, command: CommandObject, l10n: FluentLocalization):
    """Обработчик команды доната звездами"""
    if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
        await message.answer(
            l10n.format_value("donate-input-error"),
            parse_mode="HTML"
        )
        return

    amount = int(command.args)

    kb = InlineKeyboardBuilder()
    kb.button(
        text=l10n.format_value("donate-button-pay", {"amount": amount}),
        pay=True
    )
    kb.button(
        text=l10n.format_value("donate-button-cancel"),
        callback_data="donate_cancel"
    )
    kb.adjust(1)

    prices = [LabeledPrice(label="XTR", amount=amount)]

    await message.answer_invoice(
        title=l10n.format_value("donate-invoice-title"),
        description=l10n.format_value("donate-invoice-description", {"amount": amount}),
        prices=prices,
        provider_token="",  # Пустой для Stars
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
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
    await callback.message.answer(
        l10n.format_value("donate-input-error"),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "start_novel")
async def start_novel(callback: CallbackQuery, l10n):
    """Начинаем новеллу"""
    await callback.message.answer(
        "Запуск новеллы... (в разработке)",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery, l10n: FluentLocalization):
    """Обработчик отмены доната"""
    await callback.answer(l10n.format_value("donate-cancel-payment"))
    await callback.message.delete()

@router.message(Command("refund"))
async def cmd_refund(message: Message, bot: Bot, command: CommandObject, l10n: FluentLocalization):
    """Обработчик команды возврата звезд"""
    t_id = command.args
    if t_id is None:
        await message.answer(
            l10n.format_value("donate-refund-input-error"),
            parse_mode="HTML"
        )
        return

    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=t_id
        )
        await message.answer(
            l10n.format_value("donate-refund-success"),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        err_text = l10n.format_value("donate-refund-code-not-found")
        if "CHARGE_ALREADY_REFUNDED" in e.message:
            err_text = l10n.format_value("donate-refund-already-refunded")
        await message.answer(
            err_text,
            parse_mode="HTML"
        )
        return

@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery, l10n: FluentLocalization):
    """Обработчик pre_checkout_query"""
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def on_successful_payment(message: Message, l10n: FluentLocalization):
    """Обработчик успешного платежа"""
    await message.answer(
        l10n.format_value(
            "donate-successful-payment",
            {"t_id": message.successful_payment.telegram_payment_charge_id}
        ),
        parse_mode="HTML",
        message_effect_id="5159385139981059251"
    )
