import structlog
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from services.novel import NovelService
from filters.chat_type import ChatTypeFilter
from filters.referral import RegularStartCommandFilter
from keyboards.menu import get_main_menu
from .base import PermissionMixin

logger = structlog.get_logger()

router = Router(name="novel")
router.message.filter(ChatTypeFilter(["private"]))

PRIORITIES = {
    "COMMAND": 5,
    "MENU": 4,
    "CALLBACK": 3,
    "TEXT": 1
}

MENU_COMMANDS = {
    "🎮 Новелла",
    "🔄 Рестарт",
    "📖 Продолжить"
}

class NovelHandlers(PermissionMixin):
    """Обработчики команд новеллы"""
    
    def __init__(self, novel_service: NovelService):
        self.novel_service = novel_service
    
    async def start_novel(self, message: Message, l10n) -> None:
        """Запуск новеллы"""
        user_id = message.from_user.id
        logger.info(f"Starting novel for user {user_id}")
        
        try:
            novel_state = await self.novel_service.create_novel_state(user_id)
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
            
            await self.novel_service.process_message(
                message=message,
                novel_state=novel_state,
                initial_message=True
            )
            await loading_message.delete()
            
        except Exception as e:
            logger.error(f"Error starting novel: {e}", exc_info=True)
            await message.answer(l10n.format_value("novel-error"))
    
    async def handle_message(self, message: Message) -> None:
        """Обработка сообщений в новелле"""
        try:
            novel_state = await self.novel_service.get_novel_state(message.from_user.id)
            if not novel_state:
                await message.answer(
                    "У вас нет активной новеллы. Нажмите '🎮 Новелла' чтобы начать.",
                    reply_markup=get_main_menu(has_active_novel=False)
                )
                return
                
            await self.novel_service.process_message(
                message=message,
                novel_state=novel_state,
                initial_message=False
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await message.answer("Произошла ошибка при обработке сообщения")

# Инициализация обработчиков
novel_handlers = NovelHandlers(novel_service=None)  # Инициализируется через DI

@router.message(Command("start"), RegularStartCommandFilter())
async def cmd_start(message: Message, novel_service: NovelService, l10n):
    """Обработчик обычной команды /start"""
    global novel_handlers
    novel_handlers = NovelHandlers(novel_service)
    
    is_admin, is_owner = await novel_handlers.check_permissions(message)
    if not (is_admin or is_owner):
        if not await novel_handlers.check_subscription(message, l10n):
            return
    
    await novel_handlers.start_novel(message, l10n)

@router.message(F.text.in_(MENU_COMMANDS))
async def handle_menu_command(message: Message, novel_service: NovelService, l10n):
    """Обработчик команд меню"""
    global novel_handlers
    novel_handlers = NovelHandlers(novel_service)
    
    is_admin, is_owner = await novel_handlers.check_permissions(message)
    if not (is_admin or is_owner):
        if not await novel_handlers.check_subscription(message, l10n):
            return
    
    command = message.text
    if command in {"🎮 Новелла", "🔄 Рестарт"}:
        await novel_handlers.start_novel(message, l10n)
    elif command == "📖 Продолжить":
        await novel_handlers.handle_message(message)

@router.message(F.text)
async def handle_text(message: Message, novel_service: NovelService):
    """Обработчик текстовых сообщений"""
    global novel_handlers
    novel_handlers = NovelHandlers(novel_service)
    await novel_handlers.handle_message(message)
