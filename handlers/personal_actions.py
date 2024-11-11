import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from fluent.runtime import FluentLocalization
from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard
from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from middlewares.check_subscription import check_subscription
from keyboards.menu import get_main_menu
from services.novel import NovelService
from handlers.novel import start_novel_common  # Добавляем в начало файла
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from utils.referral import get_user_ref_link, create_ref_link  # Добавляем импорт

logger = structlog.get_logger()

# Declare router
router = Router()
router.message.filter(ChatTypeFilter(["private"]))

# В начале файла добавим константу
RESTART_COST = 10  # Стоимость рестарта новеллы в Stars

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(message: Message, session: AsyncSession, l10n):
    """
    Этот хэндлер будет вызван только для обычной команды /start без реферального кода
    """
    # Проверяем, является ли пользователь админом или владельцем
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    novel_service = NovelService(session)
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    # Проверяем, завершил ли пользователь новеллу ранее
    if novel_state and novel_state.is_completed and not is_admin:  # Добавляем проверку not is_admin
        # Отправляем счет на оплату рестарта только обычным пользователям
        await send_restart_invoice(message, l10n)
        return
    
    if is_admin:
        await message.answer(
            l10n.format_value("hello-msg"),
            reply_markup=get_main_menu(has_active_novel=bool(novel_state), is_admin=True),
            parse_mode="HTML"
        )
        return
    
    # Для обычных пользователей проверяем статус подписки
    is_subscribed = await IsSubscribedFilter()(message)
    
    # Выбираем нужную клавиатуру
    reply_markup = get_main_menu(has_active_novel=bool(novel_state)) if is_subscribed else await get_subscription_keyboard(message, is_subscribed=False)
    
    await message.answer(
        l10n.format_value("hello-msg"),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@router.message(F.text == "🎮 Новелла")
async def menu_novel(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Новелла"""
    # Проверяем, является ли пользователь админом или владельцем
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    if is_admin:
        await start_novel_common(message, session, l10n)
        return
        
    # Для обычных пользователей проверяем подписку
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    novel_service = NovelService(session)
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    # Проверяем, завершил ли пользователь новеллу ранее
    if novel_state and novel_state.is_completed:
        # Отправляем счет на оплату рестарта
        await send_restart_invoice(message, l10n)
        return
    
    await start_novel_common(message, session, l10n)

@router.message(F.text == "💝 Донат")
async def menu_donate(message: Message, l10n):
    """Обработчик кнопки Донат"""
    await message.answer(
        l10n.format_value("donate-input-error"),
        parse_mode="HTML"
    )

@router.message(F.text == "🔄 Рестарт")
async def menu_restart(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Рестарт"""
    # Проверяем, является ли пользователь админом или владельцем
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    if is_admin:
        await start_novel_common(message, session, l10n)
        return
        
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    # Получаем состояние новеллы
    novel_service = NovelService(session)
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    # Проверяем необходимость оплаты
    if novel_state and novel_state.needs_payment:
        # Отправляем счет на оплату рестарта
        await send_restart_invoice(message, l10n)
    else:
        # Если оплата не требуется, запускаем новеллу
        await start_novel_common(message, session, l10n)

@router.message(F.text == "❓ Помощь")
async def menu_help(message: Message, l10n):
    """Обработчик кнопки Помощь"""
    await message.answer(
        l10n.format_value("help"),
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
async def check_subscription_callback(callback: CallbackQuery, session: AsyncSession, l10n):
    """
    Этот хэндлер будет выван, когда пользователь нажмет на кнопку проверки подписки
    """
    if await IsSubscribedFilter()(callback.message):
        await callback.message.delete()
        
        # Поверяем наличие активной новеллы
        novel_service = NovelService(session)
        novel_state = await novel_service.get_novel_state(callback.from_user.id)
        
        # Создаем еню в зависимости от наличия активной новеллы
        menu = get_main_menu(has_active_novel=bool(novel_state))
        
        await callback.message.answer(
            l10n.format_value("subscription-confirmed"),
            reply_markup=menu
        )
    else:
        await callback.answer(
            l10n.format_value("subscription-check-failed"),
            show_alert=True
        )

@router.callback_query(F.data == "show_donate")
async def show_donate_info(callback: CallbackQuery, l10n):
    """Показываем информацию о донате"""
    await callback.message.answer(
        l10n.format_value("donate-input-error"),
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
async def on_successful_payment(message: Message, session: AsyncSession, l10n: FluentLocalization):
    """Обработчик успешного платежа"""
    if message.successful_payment.invoice_payload.startswith("restart_"):
        # Получаем состояние новеллы
        novel_service = NovelService(session)
        novel_state = await novel_service.get_novel_state(message.from_user.id)
        
        if novel_state:
            # Сбрасываем флаги перед запуском новой новеллы
            novel_state.needs_payment = False
            novel_state.is_completed = False
            await session.commit()
        
        # Запускаем новеллу заново
        await start_novel_common(message, session, l10n)
    else:
        # Обычный донат
        await message.answer(
            l10n.format_value(
                "donate-successful-payment",
                {"t_id": message.successful_payment.telegram_payment_charge_id}
            ),
            parse_mode="HTML",
            message_effect_id="5159385139981059251"
        )

@router.message(F.text == "📖 Продолжить")
async def menu_continue(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Продолжить"""
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    novel_service = NovelService(session)
    user_id = message.from_user.id
    
    try:
        novel_state = await novel_service.get_novel_state(user_id)
        if not novel_state:
            await message.answer("У вас нет активной новеллы. Нажмите '🎮 Новелла' чтобы начать.")
            return
            
        last_message = await novel_service.get_last_assistant_message(novel_state)
        if last_message:
            await message.answer(last_message)
        else:
            await message.answer("Не удалось найти последнее сообщение. Попробуйте наисать что-нибудь, чтобы продолжить.")
            
    except Exception as e:
        logger.error(f"Error in menu_continue: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте ещё раз.")

async def send_restart_invoice(message: Message, l10n: FluentLocalization):
    """Отправляет счет на оплату рестарта новеллы"""
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

    prices = [LabeledPrice(label="XTR", amount=RESTART_COST)]
    
    await message.answer_invoice(
        title=l10n.format_value("restart-invoice-title"),
        description=l10n.format_value("restart-invoice-description"),
        prices=prices,
        provider_token="",  # Пустой для Stars
        payload=f"restart_{RESTART_COST}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "restart_cancel")
async def on_restart_cancel(callback: CallbackQuery, l10n: FluentLocalization):
    """Обработчик отмены рестарта"""
    await callback.answer(l10n.format_value("restart-cancel-payment"))
    await callback.message.delete()

@router.message(F.text == "🔗 Реферальная ссылка")
async def menu_ref_link(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Реферальная ссылка"""
    # Проверяем подписку
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
        
    try:
        # Получаем существующую ссылку или создаем новую
        ref_link = await get_user_ref_link(session, message.from_user.id)
        if not ref_link:
            ref_link = await create_ref_link(session, message.from_user.id)
            
        # Формируем ссылку для бота
        bot_username = (await message.bot.me()).username
        invite_link = f"https://t.me/{bot_username}?start=ref_{ref_link.code}"
        
        await message.answer(
            l10n.format_value(
                "referral-link-msg",
                {
                    "link": invite_link,
                    "reward": "награду"  # или другая награда
                }
            ),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error generating referral link: {e}")
        await message.answer(
            l10n.format_value("referral-link-error"),
            parse_mode="HTML"
        )
