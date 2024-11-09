import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from fluent.runtime import FluentLocalization
from filters.is_subscribed import IsSubscribedFilter
from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from keyboards.menu import get_main_menu
from keyboards.admin import get_admin_menu
from keyboards.subscription import get_subscription_keyboard
from services.novel import NovelService
from services.admin import AdminService
from services.payment import PaymentService
from services.referral import ReferralService
from handlers.novel import start_novel_common
from handlers.payments import send_restart_invoice, send_donate_invoice

logger = structlog.get_logger()

router = Router(name="personal_actions")
router.message.filter(ChatTypeFilter(["private"]))

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization,
    state: FSMContext
) -> None:
    """Обработчик команды /start"""
    await state.clear()
    
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    if novel_state and novel_state.is_completed and not is_admin:
        await send_restart_invoice(message, l10n)
        return
    
    if is_admin:
        await message.answer(
            text=l10n.format_value("hello-msg"),
            reply_markup=get_admin_menu(has_active_novel=bool(novel_state)),
            parse_mode="HTML"
        )
        return
    
    is_subscribed = await IsSubscribedFilter()(message)
    reply_markup = get_main_menu(has_active_novel=bool(novel_state)) if is_subscribed else await get_subscription_keyboard(message)
    
    await message.answer(
        text=l10n.format_value("hello-msg"),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Статистика")
async def menu_stats(
    message: Message,
    admin_service: AdminService,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Статистика"""
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    if not is_admin:
        return
        
    try:
        stats = await admin_service.get_statistics()
        await message.answer(
            text=l10n.format_value("stats-msg", stats),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        await message.answer(
            text=l10n.format_value("error-general"),
            parse_mode="HTML"
        )

@router.message(F.text == "🗑 Очистить базу")
async def menu_clear_db(
    message: Message,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Очистить базу"""
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    if not is_admin:
        return
        
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="clear_db_confirm")
    kb.button(text="❌ Нет", callback_data="clear_db_cancel")
    kb.adjust(2)
    
    await message.answer(
        text=l10n.format_value("clear-db-confirm"),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "clear_db_confirm")
async def on_clear_db_confirm(
    callback: CallbackQuery,
    admin_service: AdminService,
    l10n: FluentLocalization,
    state: FSMContext
) -> None:
    """Обработчик подтверждения очистки базы"""
    is_admin = await IsAdminFilter(is_admin=True)(callback.message) or await IsOwnerFilter(is_owner=True)(callback.message)
    if not is_admin:
        return
        
    try:
        await admin_service.clear_database()
        await state.clear()
        await callback.message.edit_text(
            text=l10n.format_value("clear-db-success"),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        await callback.message.edit_text(
            text=l10n.format_value("error-general"),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "clear_db_cancel")
async def on_clear_db_cancel(
    callback: CallbackQuery,
    l10n: FluentLocalization
) -> None:
    """Обработчик отмены очистки базы"""
    is_admin = await IsAdminFilter(is_admin=True)(callback.message) or await IsOwnerFilter(is_owner=True)(callback.message)
    if not is_admin:
        return
        
    await callback.message.edit_text(
        text=l10n.format_value("clear-db-cancelled"),
        parse_mode="HTML"
    )

@router.pre_checkout_query()
async def pre_checkout_query(
    query: PreCheckoutQuery,
    l10n: FluentLocalization
) -> None:
    """Обработчик pre_checkout_query"""
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    novel_service: NovelService,
    payment_service: PaymentService,
    l10n: FluentLocalization
) -> None:
    """Обработчик успешного платежа"""
    try:
        if message.successful_payment.invoice_payload.startswith("restart_"):
            novel_state = await novel_service.get_novel_state(message.from_user.id)
            if novel_state:
                await payment_service.process_restart_payment(novel_state)
                await novel_service.start_novel(message)
        else:
            await message.answer(
                text=l10n.format_value(
                    "donate-successful-payment",
                    {"t_id": message.successful_payment.telegram_payment_charge_id}
                ),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await message.answer(
            text=l10n.format_value("error-general"),
            parse_mode="HTML"
        )

@router.message(F.text == "🎮 Новелла")
async def menu_novel(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Новелла"""
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    if is_admin:
        await start_novel_common(message, novel_service, l10n)
        return
        
    if not await IsSubscribedFilter()(message):
        await message.answer(
            text=l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    if novel_state and novel_state.is_completed:
        await send_restart_invoice(message, l10n)
        return
    
    await start_novel_common(message, novel_service, l10n)

@router.message(F.text == "📖 Продолжить")
async def menu_continue(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Продолжить"""
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    if not is_admin and not await IsSubscribedFilter()(message):
        await message.answer(
            text=l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
        
    try:
        novel_state = await novel_service.get_novel_state(message.from_user.id)
        if not novel_state:
            await message.answer(
                text=l10n.format_value("novel-not-started"),
                parse_mode="HTML"
            )
            return
            
        last_message = await novel_service.get_last_assistant_message(novel_state)
        if last_message:
            await message.answer(
                text=last_message,
                parse_mode="HTML"
            )
        else:
            await message.answer(
                text=l10n.format_value("novel-no-last-message"),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error in menu_continue: {e}")
        await message.answer(
            text=l10n.format_value("error-general"),
            parse_mode="HTML"
        )

@router.message(F.text == "🔄 Рестарт")
async def menu_restart(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Рестарт"""
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    if is_admin:
        await start_novel_common(message, novel_service, l10n)
        return
        
    if not await IsSubscribedFilter()(message):
        await message.answer(
            text=l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
        
    await send_restart_invoice(message, l10n)

@router.message(F.text == "🔗 Реферальная ссылка")
async def menu_ref_link(
    message: Message,
    referral_service: ReferralService,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Реферальная ссылка"""
    if not await IsSubscribedFilter()(message):
        await message.answer(
            text=l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
        
    try:
        ref_link = await referral_service.get_or_create_ref_link(message.from_user.id)
        bot_username = (await message.bot.me()).username
        invite_link = f"https://t.me/{bot_username}?start=ref_{ref_link}"
        
        await message.answer(
            text=l10n.format_value("referral-link-msg", {"link": invite_link}),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error getting referral link: {e}")
        await message.answer(
            text=l10n.format_value("error-general"),
            parse_mode="HTML"
        )

@router.message(F.text == "💝 Донат")
async def menu_donate(
    message: Message,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Донат"""
    kb = InlineKeyboardBuilder()
    kb.button(text="10 Stars", callback_data="donate_10")
    kb.button(text="20 Stars", callback_data="donate_20")
    kb.button(text="50 Stars", callback_data="donate_50")
    kb.button(text="100 Stars", callback_data="donate_100")
    kb.adjust(2)
    
    await message.answer(
        text=l10n.format_value("donate-choose-amount"),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.message(F.text == "❓ Помощь")
async def menu_help(
    message: Message,
    l10n: FluentLocalization
) -> None:
    """Обработчик кнопки Помощь"""
    await message.answer(
        text=l10n.format_value("help-msg"),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("donate_"))
async def on_donate_amount(
    callback: CallbackQuery,
    l10n: FluentLocalization
) -> None:
    """Обработчик выбора суммы доната"""
    amount = int(callback.data.split("_")[1])
    await send_donate_invoice(callback.message, amount, l10n)
    await callback.message.delete()
        