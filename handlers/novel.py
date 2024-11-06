import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.novel import NovelService
from filters.chat_type import ChatTypeFilter
from filters.is_subscribed import IsSubscribedFilter
from filters.is_admin import IsAdminFilter
from filters.is_owner import IsOwnerFilter
from middlewares.check_subscription import check_subscription
from keyboards.subscription import get_subscription_keyboard
from keyboards.menu import get_main_menu
from utils.openai_helper import openai_client

logger = structlog.get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

RESTART_COST = 10  # Стоимость перезапуска в звездах

async def start_novel_common(message: Message, session: AsyncSession, l10n):
    """Общая логика запуска новеллы"""
    user_id = message.from_user.id
    novel_service = NovelService(session)
    
    try:
        # Создаём новое состояние новеллы
        novel_state = await novel_service.create_novel_state(user_id)
        
        # Если вернулся None - значит требуется оплата
        if novel_state is None:
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
        
        # Отправляем первое сообщение в тред и обрабатываем его
        await openai_client.beta.threads.messages.create(
            thread_id=novel_state.thread_id,
            role="user",
            content="Начни с шага '0. Инициализация:' и спроси моё имя."
        )
        
        # Начинаем новеллу
        await novel_service.process_message(
            message=message,
            novel_state=novel_state,
            initial_message=True  # Флаг для первого сообщения
        )
        
        # Удаляем сообщение о загрузке
        await loading_message.delete()
        
    except Exception as e:
        logger.error(f"Error starting novel: {e}")
        await message.answer(l10n.format_value("novel-error"))

@router.callback_query(F.data == "start_novel")
@check_subscription
async def start_novel_button(callback: CallbackQuery, session: AsyncSession, l10n):
    """Запуск новеллы через кнопку"""
    # Не удаляем сообщение, просто запускаем новеллу
    await start_novel_common(callback.message, session, l10n)
    await callback.answer()  # Закрываем уведомление о нажатии

@router.message(F.text == "🎮 Новелла")
async def menu_novel(message: Message, session: AsyncSession, l10n):
    """Обработчик кнопки Новелла"""
    # Проверяем, является ли пользователь админом или владельцем
    if await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter(is_owner=True)(message):
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
    
    # Проверяем, нужна ли оплата
    novel_service = NovelService(session)
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    
    if novel_state and novel_state.needs_payment:
        # Создаем клавиатуру для доната
        kb = InlineKeyboardBuilder()
        kb.button(
            text=l10n.format_value("donate-button-pay", {"amount": 10}),
            pay=True
        )
        kb.button(
            text=l10n.format_value("donate-button-cancel"),
            callback_data="donate_cancel"
        )
        kb.adjust(1)

        # Отправляем инвойс
        await message.answer_invoice(
            title="Повторное прохождение новеллы",
            description="Оплата за возможность пройти новеллу еще раз",
            prices=[LabeledPrice(label="XTR", amount=10)],
            provider_token="",  # Пустой для Stars
            payload="novel_restart",
            currency="XTR",
            reply_markup=kb.as_markup()
        )
        return
    
    await start_novel_common(message, session, l10n)

@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession, l10n):
    """Обработчик успешного платежа"""
    if message.successful_payment.invoice_payload == "novel_restart":
        # Сбрасываем флаг необходимости оплаты
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

@router.message(F.text == "🔄 Рестарт")
async def restart_novel(message: Message, session: AsyncSession, l10n):
    """Перезапуск новеллы через кнопку меню"""
    # Проверяем, является ли пользователь админом или владельцем
    if await IsAdminFilter(is_admin=True)(message) or await IsOwnerFilter()(message):
        await start_novel_common(message, session, l10n)
        return
        
    # Для обычных пользователей проверяем подписку
    if not await IsSubscribedFilter()(message):
        await message.answer(
            l10n.format_value("subscription-required"),
            reply_markup=await get_subscription_keyboard(message)
        )
        return
    
    await start_novel_common(message, session, l10n)

@router.message(F.text)
async def handle_message(message: Message, session: AsyncSession):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    novel_service = NovelService(session)
    
    try:
        # Получаем состояние новеллы
        novel_state = await novel_service.get_novel_state(user_id)
        if not novel_state:
            await message.answer("Пожалуйста, нажмите кнопку 'Запустить новеллу'")
            return
            
        # Обрабатываем сообщение
        await novel_service.process_message(
            message=message,
            novel_state=novel_state
        )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await message.answer("Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте ещё раз.")
        