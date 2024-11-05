import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.novel import NovelService
from filters.chat_type import ChatTypeFilter
from filters.is_subscribed import IsSubscribedFilter
from middlewares.check_subscription import check_subscription
from keyboards.subscription import get_subscription_keyboard
from keyboards.menu import get_main_menu
from utils.openai_helper import openai_client

logger = structlog.get_logger()

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

async def start_novel_common(message: Message, session: AsyncSession, l10n):
    """Общая логика запуска новеллы"""
    user_id = message.from_user.id
    novel_service = NovelService(session)
    
    try:
        # Удаляем старое состояние, если оно есть
        old_state = await novel_service.get_novel_state(user_id)
        if old_state:
            await novel_service.end_story(old_state, message, silent=True)
        
        # Создаём новое состояние новеллы
        novel_state = await novel_service.create_novel_state(user_id)
        
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

@router.message(F.text == "🔄 Рестарт")
async def restart_novel(message: Message, session: AsyncSession, l10n):
    """Перезапуск новеллы через кнопку меню"""
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
        