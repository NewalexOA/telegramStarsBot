import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from services.novel import NovelService
from filters.chat_type import ChatTypeFilter
from keyboards.menu import get_main_menu
from filters.referral import RegularStartCommandFilter
from filters.is_admin import IsAdminFilter
from handlers.personal_actions import show_help

logger = structlog.get_logger()

router = Router(name="novel")
router.message.filter(ChatTypeFilter(["private"]))

# Константы для приоритетов
PRIORITIES = {
    "COMMAND": 5,
    "MENU": 4,
    "CALLBACK": 3,
    "TEXT": 1
}

# Все команды меню
MENU_COMMANDS = {
    # Основные кнопки
    "🎮 Новелла",
    "📖 Продолжить",
    "🔄 Рестарт",
    # Админские кнопки
    "📊 Статистика",
    "🗑 Очистить базу",
    # Общие кнопки
    "🔗 Реферальная ссылка",
    "💝 Донат",
    "❓ Помощь"
}

async def start_novel_common(message: Message, novel_service: NovelService, l10n) -> None:
    """Общая логика запуска новеллы"""
    user_id = message.from_user.id
    logger.info(f"Starting novel for user {user_id}")
    
    try:
        # Создаём новое состояние новеллы
        novel_state = await novel_service.create_novel_state(user_id)
        if not novel_state:
            await message.answer(
                l10n.format_value("novel-payment-required"),
                reply_markup=get_main_menu(has_active_novel=False)
            )
            return
            
        await message.answer(
            l10n.format_value("novel-started"),
            reply_markup=get_main_menu(has_active_novel=True)
        )
        loading_message = await message.answer("⌛️ Загрузка истории...")
        
        await novel_service.process_message(
            message=message,
            novel_state=novel_state,
            initial_message=True
        )
        await loading_message.delete()
        
    except Exception as e:
        logger.error(f"Error starting novel: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

async def continue_novel(message: Message, novel_service: NovelService, l10n) -> None:
    """Продолжение существующей новеллы"""
    try:
        novel_state = await novel_service.get_novel_state(message.from_user.id)
        if not novel_state:
            await message.answer(
                l10n.format_value("no-active-novel"),
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
                l10n.format_value("no-last-message"),
                reply_markup=get_main_menu(has_active_novel=True)
            )
            
    except Exception as e:
        logger.error(f"Error continuing novel: {e}", exc_info=True)
        await message.answer(l10n.format_value("novel-error"))

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(message: Message, novel_service: NovelService, l10n):
    """Обработчик команды /start"""
    await start_novel_common(message, novel_service, l10n)

@router.message(F.text.in_(MENU_COMMANDS), flags={"priority": PRIORITIES["MENU"]})
async def handle_menu_command(message: Message, novel_service: NovelService, l10n):
    """Обработчик команд меню"""
    command = message.text
    
    # Проверяем права для админских команд
    if command in {"📊 Статистика", "🗑 Очистить базу"}:
        is_admin = await IsAdminFilter(is_admin=True)(message)
        if not is_admin:
            return
            
    # Обработка команд
    if command in {"🎮 Новелла", "🔄 Рестарт"}:
        await start_novel_common(message, novel_service, l10n)
    elif command == "📖 Продолжить":
        await continue_novel(message, novel_service, l10n)
    elif command == "❓ Помощь":
        await show_help(message, l10n)
    # Остальные команды обрабатываются в своих хендлерах

@router.message(F.text, flags={"priority": PRIORITIES["TEXT"]})
async def handle_text(message: Message, novel_service: NovelService):
    """Обработчик текстовых сообщений"""
    novel_state = await novel_service.get_novel_state(message.from_user.id)
    if not novel_state:
        return
        
    await novel_service.process_message(
        message=message,
        novel_state=novel_state,
        initial_message=False
    )
