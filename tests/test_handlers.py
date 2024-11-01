import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, User
from aiogram import Bot
from handlers.referral import cmd_get_ref_link, cmd_start_with_ref

@pytest.mark.asyncio
async def test_ref_command(db_session):
    """Test referral command handler"""
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock(spec=User)
    message.from_user.id = 123456
    
    # Создаем мок для bot.me()
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.me.return_value = AsyncMock(username="test_bot")
    message.bot = mock_bot
    
    # Создаем мок для message.answer
    message.answer = AsyncMock()
    
    await cmd_get_ref_link(message, db_session)
    
    message.answer.assert_called_once()
    assert "https://t.me/test_bot?start=ref_" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_start_with_ref(db_session):
    """Test start command with referral"""
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock(spec=User)
    message.from_user.id = 123456
    message.text = "/start ref_testcode"
    
    # Создаем мок для message.answer
    message.answer = AsyncMock()
    
    await cmd_start_with_ref(message, db_session)
    
    message.answer.assert_called_once_with("Добро пожаловать!")