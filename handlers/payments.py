import structlog
from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, CommandObject

from services.novel import NovelService
from services.payment import PaymentService
from config_reader import get_config, BotConfig

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

router = Router(name="payments")

RESTART_COST = 10

async def send_donate_invoice(message: Message, amount: int, l10n):
    """Отправляет счет для доната"""
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

    await message.answer_invoice(
        title=l10n.format_value("donate-invoice-title"),
        description=l10n.format_value("donate-invoice-description", {"amount": amount}),
        prices=[LabeledPrice(label="XTR", amount=amount)],
        provider_token=bot_config.provider_token,
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработчик предварительной проверки платежа"""
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message,
    novel_service: NovelService,
    payment_service: PaymentService,
    l10n
):
    """Обработчик успешного платежа"""
    try:
        await payment_service.process_payment(
            user_id=message.from_user.id,
            payload=message.successful_payment.invoice_payload,
            amount=message.successful_payment.total_amount,
            novel_service=novel_service
        )
        
        await message.answer(
            l10n.format_value("payment-success"),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error processing payment: {e}", exc_info=True)
        await message.answer(l10n.format_value("payment-error"))

async def send_restart_invoice(message: Message, l10n):
    """Отправляет инвойс для оплаты рестарта новеллы"""
    kb = InlineKeyboardBuilder()
    kb.button(
        text=l10n.format_value("restart-button-pay", {"amount": RESTART_COST}),
        pay=True
    )
    kb.button(
        text=l10n.format_value("restart-button-cancel"),
        callback_data="restart_cancel"
    )
    kb.adjust(1)

    await message.answer_invoice(
        title=l10n.format_value("restart-invoice-title"),
        description=l10n.format_value("restart-invoice-description"),
        prices=[LabeledPrice(label="XTR", amount=RESTART_COST)],
        provider_token=bot_config.provider_token,
        payload="novel_restart",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

@router.message(Command("donate", "donat", "донат"))
async def cmd_donate(message: Message, command: CommandObject, l10n):
    """Обработчик команды доната звездами"""
    try:
        if command.args is None or not command.args.isdigit() or not 1 <= int(command.args) <= 2500:
            await message.answer(
                l10n.format_value("donate-input-error"),
                parse_mode="HTML"
            )
            return

        amount = int(command.args)
        await send_donate_invoice(message, amount, l10n)
        
    except Exception as e:
        logger.error(f"Error processing donate command: {e}", exc_info=True)
        await message.answer(l10n.format_value("donate-input-error"))