from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from fluent.runtime import FluentLocalization
from filters.is_owner import IsOwnerFilter

# Declare router
router = Router()

# Создаем отдельный роутер для команд без проверки на владельца
common_router = Router()

# Основные команды с проверкой на владельца
router.message.filter(IsOwnerFilter(is_owner=True))

# Handlers:
@router.message(Command("start"))
async def cmd_owner_hello(message: Message, l10n: FluentLocalization):
    """Приветствие для владельца"""
    await message.answer(
        l10n.format_value("hello-owner"),
        parse_mode="HTML"
    )

@router.message(
    IsOwnerFilter(is_owner=True),
    Command(commands=["ping"]),
)
async def cmd_ping_bot(message: Message, l10n: FluentLocalization):
    await message.reply(
        l10n.format_value("ping-msg"),
        parse_mode="HTML"
    )

# Команда без проверки на владельца
@common_router.message(Command("chatid"))
async def cmd_get_chat_id(message: Message):
    """Обработчик для получения ID чата"""
    if message.forward_from_chat:
        await message.answer(
            f"Chat ID: {message.forward_from_chat.id}\n"
            f"Type: {message.forward_from_chat.type}\n"
            f"Title: {message.forward_from_chat.title}"
        )
    else:
        await message.answer(
            f"Current chat ID: {message.chat.id}\n"
            f"Type: {message.chat.type}"
        )
