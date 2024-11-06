import structlog
from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import TelegramBadRequest

from services.novel import NovelService
from filters.chat_type import ChatTypeFilter
from filters.is_subscribed import IsSubscribedFilter
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from middlewares.check_subscription import check_subscription
from keyboards.subscription import get_subscription_keyboard
from keyboards.menu import get_main_menu
from filters.referral import RegularStartCommandFilter
from utils.referral_processor import process_referral
from utils.referral import create_ref_link
from config_reader import get_config, BotConfig

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

router = Router(name="novel")
router.message.filter(ChatTypeFilter(["private"]))

# Константы для приоритетов
PRIORITIES = {
    "COMMAND": 9,
    "ADMIN": 8,
    "MENU": 7,
    "CALLBACK": 6,
    "PAYMENT": 5,
    "TEXT": 4
}

RESTART_COST = 10

MENU_COMMANDS = {
    "🎮 Новелла",
    "🔄 Рестарт",
    "💝 Донат",
    "❓ Помощь",
    "🔗 Реферальная ссылка",
    "📖 Продолжить"
}

DONATE_COMMANDS = {"/donate", "/donat", "/донат"}

async def check_user_permissions(message: Message) -> tuple[bool, bool]:
    """Проверка прав пользователя"""
    is_admin = await IsAdminFilter(is_admin=True)(message)
    is_owner = await IsOwnerFilter(is_owner=True)(message)
    return is_admin, is_owner

async def check_subscription_required(message: Message, l10n) -> bool:
    """Проверка подписки для обычных пользователей"""
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return False
    return True

async def start_novel_common(message: Message, session: AsyncSession, l10n):
    """Общая логика запуска новеллы"""
    user_id = message.from_user.id
    logger.info(f"Starting novel common for user {user_id}")
    
    novel_service = NovelService(session)
    
    try:
        # Создаём новое состояние новеллы
        novel_state = await novel_service.create_novel_state(user_id)
        logger.info(f"Created novel state {novel_state.id if novel_state else None} for user {user_id}")
        
        # Если вернулся None - значит требуется оплата
        if novel_state is None:
            logger.info(f"Payment required for user {user_id}")
            await message.answer(
                "Для повторного прохождения новеллы требуется оплата.",
                reply_markup=get_main_menu(has_active_novel=False)
            )
            return
        
        # Отправляем основное меню и сообщение о загрузке
        await message.answer(
            "Новелла начинается! Используйте меню для управления:",
            reply_markup=get_main_menu(has_active_novel=True)
        )
        loading_message = await message.answer("⌛️ Загрузка истории...")
        
        logger.info(f"Processing initial message for user {user_id}")
        # Начинаем новеллу
        await novel_service.process_message(
            message=message,
            novel_state=novel_state,
            initial_message=True  # Флаг для первого сообщения
        )
        
        # Удаляем сообщение о загрузке
        await loading_message.delete()
        
    except Exception as e:
        logger.error(f"Error starting novel: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

# Команды
@router.message(
    Command("start"),
    ~RegularStartCommandFilter(),
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["COMMAND"]}
)
async def cmd_start_ref(message: Message, session: AsyncSession, l10n):
    """Обработчик команды /start с реферальной ссылкой"""
    try:
        ref_code = message.text.split()[1].replace('ref_', '')
        await process_referral(session, ref_code, message.from_user.id, message)
        await cmd_start(message, session, l10n)
    except (IndexError, ValueError) as e:
        logger.error(f"Error processing referral: {e}")
        await cmd_start(message, session, l10n)
    except Exception as e:
        logger.error(f"Unexpected error in cmd_start_ref: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

@router.message(
    Command("start"),
    RegularStartCommandFilter(),
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["COMMAND"]}
)
async def cmd_start(message: Message, session: AsyncSession, l10n):
    """Обработчик обычной команды /start"""
    try:
        await message.answer(
            l10n.format_value("hello-msg"),
            reply_markup=get_main_menu(has_active_novel=False),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

@router.message(
    F.text.in_(MENU_COMMANDS),
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["MENU"]}
)
async def handle_menu_command(message: Message, session: AsyncSession, l10n):
    """Общий обработчик команд меню"""
    try:
        command = message.text
        user_id = message.from_user.id
        is_admin, is_owner = await check_user_permissions(message)
        
        if command == "🎮 Новелла":
            if not (is_admin or is_owner):
                if not await check_subscription_required(message, l10n):
                    return
            await start_novel_common(message, session, l10n)
            
        elif command == "🔄 Рестарт":
            novel_service = NovelService(session)
            novel_state = await novel_service.get_novel_state(user_id)
            
            if not (is_admin or is_owner):
                if not await check_subscription_required(message, l10n):
                    return
                if novel_state and novel_state.needs_payment:
                    await send_restart_invoice(message, l10n)
                    return
            
            await start_novel_common(message, session, l10n)
            
        elif command == "💝 Донат":
            await menu_donate(message, l10n)
            
        elif command == "❓ Помощь":
            await menu_help(message, l10n)
            
        elif command == "🔗 Реферальная ссылка":
            await menu_referral(message, session, l10n)
            
        elif command == "📖 Продолжить":
            if not await check_subscription_required(message, l10n):
                return
                
            novel_service = NovelService(session)
            novel_state = await novel_service.get_novel_state(user_id)
            
            if not novel_state:
                await message.answer(
                    "У вас нет активной новеллы. Нажмите '🎮 Новелла' чтобы начать.",
                    reply_markup=get_main_menu(has_active_novel=False)
                )
                return
                
            last_message = await novel_service.get_last_assistant_message(novel_state)
            if last_message:
                await message.answer(
                    last_message,
                    reply_markup=get_main_menu(has_active_novel=True)
                )
            else:
                await message.answer(
                    "Не удалось найти последнее сообщение. Попробуйте написать что-нибудь, чтобы продолжить.",
                    reply_markup=get_main_menu(has_active_novel=True)
                )
            
    except Exception as e:
        logger.error(f"Error in handle_menu_command: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

@router.message(
    Command("donate", "donat", "донат"),
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["COMMAND"]}
)
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

# Кнопки меню
@router.message(
    F.text.in_({"🎮 Новелла", "🔄 Рестарт"}),
    flags={"priority": PRIORITIES["MENU"]}
)
async def handle_menu_buttons(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопок меню новеллы"""
    try:
        user_id = message.from_user.id
        is_admin, is_owner = await check_user_permissions(message)
        
        if message.text == "🔄 Рестарт":
            if not (is_admin or is_owner):
                await message.answer("У вас нет прав для рестарта новеллы")
                return
                
            novel_service = NovelService(session)
            novel_state = await novel_service.get_novel_state(user_id)
            
            if novel_state and novel_state.needs_payment:
                await send_restart_invoice(message, l10n)
                return
        
        if not (is_admin or is_owner):
            if not await check_subscription_required(message, l10n):
                return
        
        await start_novel_common(message, session, l10n)
        
    except Exception as e:
        logger.error(f"Error in handle_menu_buttons: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды")

@router.message(
    F.text == "💝 Донат",
    flags={"priority": PRIORITIES["MENU"]}
)
async def menu_donate(message: Message, l10n):
    """Обработчик кнопки Донат"""
    await message.answer(
        l10n.format_value("donate-input-error"),
        parse_mode="HTML"
    )

@router.message(
    F.text == "❓ Помощь",
    flags={"priority": PRIORITIES["MENU"]}
)
async def menu_help(message: Message, l10n):
    """Обработчик кнопки Помощь"""
    await message.answer(
        l10n.format_value("help"),
        parse_mode="HTML"
    )

@router.message(
    F.text == "📖 Продолжить",
    flags={"priority": PRIORITIES["MENU"]}
)
async def menu_continue(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Продолжить"""
    try:
        if not await check_subscription_required(message, l10n):
            return
            
        user_id = message.from_user.id
        novel_service = NovelService(session)
        
        novel_state = await novel_service.get_novel_state(user_id)
        if not novel_state:
            await message.answer(
                "У вас нет активной новеллы. Нажмите '🎮 Новелла' чтобы начать.",
                reply_markup=get_main_menu(has_active_novel=False)
            )
            return
            
        last_message = await novel_service.get_last_assistant_message(novel_state)
        if last_message:
            await message.answer(
                last_message,
                reply_markup=get_main_menu(has_active_novel=True)
            )
        else:
            await message.answer(
                "Не удалось найти последнее сообщение. Попробуйте написать что-нибудь, чтобы продолжить.",
                reply_markup=get_main_menu(has_active_novel=True)
            )
            
    except Exception as e:
        logger.error(f"Error in menu_continue: {e}", exc_info=True)
        await message.answer("Произошла ошибка при продолжении новеллы")

# Callback-запросы
@router.callback_query(
    F.data == "start_novel",
    flags={"priority": PRIORITIES["CALLBACK"]}
)
@check_subscription
async def start_novel_button(callback: CallbackQuery, session: AsyncSession, l10n):
    """Запуск новеллы через inline кнопку"""
    try:
        await start_novel_common(callback.message, session, l10n)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in start_novel_button: {e}", exc_info=True)
        await callback.message.answer("Произошла ошибка при запуске нвеллы")

@router.callback_query(
    F.data == "restart_cancel",
    flags={"priority": PRIORITIES["CALLBACK"]}
)
async def cancel_restart(callback: CallbackQuery):
    """Отмена рестарта"""
    try:
        await callback.message.delete()
        await callback.answer("Рестарт отменен")
    except Exception as e:
        logger.error(f"Error in cancel_restart: {e}", exc_info=True)
        await callback.answer("Ошибка при отмене рестарта")

# Платежи
@router.message(
    F.successful_payment,
    flags={"priority": PRIORITIES["PAYMENT"]}
)
async def handle_successful_payment(message: Message, session: AsyncSession, l10n):
    """Обработчик успешного платежа"""
    try:
        if message.successful_payment.invoice_payload == "novel_restart":
            novel_service = NovelService(session)
            novel_state = await novel_service.get_novel_state(message.from_user.id)
            if novel_state:
                novel_state.needs_payment = False
                await session.commit()
            
            await start_novel_common(message, session, l10n)
            await message.answer(
                "Спасибо за оплату! Новелла запущена.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error processing payment: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке платежа")

# Общий обработчик текста
@router.message(
    F.text,
    ~F.text.startswith("/"),  # Игнорируем все команды
    ~F.text.in_(MENU_COMMANDS),  # Игнорируем кнопки меню
    flags={"priority": PRIORITIES["TEXT"]}
)
async def handle_message(message: Message, session: AsyncSession):
    """Обработка текстовых сообщений"""
    try:
        user_id = message.from_user.id
        novel_service = NovelService(session)
        
        novel_state = await novel_service.get_novel_state(user_id)
        if not novel_state:
            await message.answer(
                "Пожалуйста, нажмите кнопку '�� Новелла'",
                reply_markup=get_main_menu(has_active_novel=False)
            )
            return
            
        await novel_service.process_message(
            message=message,
            novel_state=novel_state,
            initial_message=False
        )
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке сообщения")

@router.message(
    F.text == "🔗 Реферальная ссылка",
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["MENU"]}
)
async def menu_referral(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Реферальная ссылка"""
    try:
        ref_link = await create_ref_link(session, message.from_user.id)
        bot_username = (await message.bot.me()).username
        full_link = f"https://t.me/{bot_username}?start=ref_{ref_link.code}"
        
        await message.answer(
            l10n.format_value("referral-link-msg", {
                "link": full_link,
                "reward": "разблокировка новой главы"
            }),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error generating referral link: {e}", exc_info=True)
        await message.answer(l10n.format_value("referral-link-error"))

# Добавляем обработчик pre_checkout_query
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработчик предварительной проверки платежа"""
    await pre_checkout_query.answer(ok=True)

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
        provider_token="",  # Пустой для Stars
        payload="novel_restart",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

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
        provider_token=bot_config.provider_token,  # Исправляем на корректный токен
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery, l10n):
    """Обработчик отмены доната"""
    await callback.answer(l10n.format_value("donate-cancel-payment"))
    await callback.message.delete()

@router.message(
    Command("refund"),
    ChatTypeFilter(["private"]),
    flags={"priority": PRIORITIES["COMMAND"]}
)
async def cmd_refund(message: Message, bot: Bot, command: CommandObject, l10n):
    """Обработчик команды возврата звезд"""
    if command.args is None:
        await message.answer(
            l10n.format_value("donate-refund-input-error"),
            parse_mode="HTML"
        )
        return

    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=command.args
        )
        await message.answer(
            l10n.format_value("donate-refund-success"),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        err_text = l10n.format_value("donate-refund-code-not-found")
        if "CHARGE_ALREADY_REFUNDED" in str(e):
            err_text = l10n.format_value("donate-refund-already-refunded")
        await message.answer(
            err_text,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error processing refund: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))
