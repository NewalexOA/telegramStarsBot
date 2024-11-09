import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluent.runtime import FluentLocalization
from filters.is_subscribed import IsSubscribedFilter
from keyboards.subscription import get_subscription_keyboard
from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from keyboards.menu import get_main_menu
from services.novel import NovelService
from services.referral import ReferralService
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter

logger = structlog.get_logger()

# Declare router
router = Router()
router.message.filter(ChatTypeFilter(["private"]))

# В начале файла добавим константу
RESTART_COST = 10  # Стоимость рестарта новеллы в Stars

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
):
    """
    Этот хэндлер будет вызван только для обычной команды /start без реферального кода
    """
    # Проверяем, является ли пользователь админом или владельцем
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    # Проверяем, завершил ли пользователь новеллу ранее
    if novel_state and novel_state.is_completed and not is_admin:
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
    reply_markup = get_main_menu(has_active_novel=bool(novel_state)) if is_subscribed else await get_subscription_keyboard(message)
    
    await message.answer(
        l10n.format_value("hello-msg"),
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

@router.message(F.text == "🎮 Новелла")
async def menu_novel(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
):
    """Обработчик кнопки Новелла"""
    # Проверяем, является ли пользователь админом или владельцем
    is_admin = await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message)
    
    if is_admin:
        await start_novel_common(message, novel_service, l10n)
        return
        
    # Для обычных пользователей проверяем подписку
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message),
            parse_mode="HTML"
        )
        return
    
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    # Проверяем, завершил ли пользователь новеллу ранее
    if novel_state and novel_state.is_completed:
        # Отправляем счет на оплату рестарта
        await send_restart_invoice(message, l10n)
        return
    
    await start_novel_common(message, novel_service, l10n)

@router.message(F.text == "🔗 Реферальная ссылка")
async def menu_ref_link(
    message: Message,
    referral_service: ReferralService,
    l10n: FluentLocalization
):
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
        link = await referral_service.create_referral_link(message.from_user.id)
        if not link:
            await message.answer(l10n.format_value("error-creating-link"))
            return
            
        # Формируем ссылку для бота
        bot_username = (await message.bot.me()).username
        invite_link = f"https://t.me/{bot_username}?start=ref_{link.code}"
        
        await message.answer(
            l10n.format_value(
                "referral-link-msg",
                {
                    "link": invite_link,
                    "reward": "награду"
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

async def send_restart_invoice(message: Message, l10n: FluentLocalization):
    """Отправляет счет для оплаты рестарта новеллы"""
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

async def start_novel_common(
    message: Message,
    novel_service: NovelService,
    l10n: FluentLocalization
):
    """Общая логика запуска новеллы"""
    user_id = message.from_user.id
    logger.info(f"Starting novel common for user {user_id}")
    
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

# ... остальные обработчики аналогично обновляются ...
