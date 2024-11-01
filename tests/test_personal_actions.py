import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User, Chat, CallbackQuery
from handlers.personal_actions import cmd_start, cmd_help, cmd_language, check_subscription_callback

# Создаем фикстуру для I18n
@pytest.fixture(autouse=True)
def setup_i18n():
    """Setup I18n for tests"""
    # Создаем мок для gettext
    def mock_gettext(text):
        # Простой мок, который возвращает тот же текст
        return text
        
    # Патчим gettext в модуле handlers.personal_actions
    with patch('handlers.personal_actions._', mock_gettext):
        yield

@pytest.mark.asyncio
async def test_cmd_start():
    """Test start command handler"""
    # Создаем мок для пользователя
    user = AsyncMock(spec=User)
    user.id = 123456
    user.full_name = "Test User"
    user.username = "test_user"

    # Создаем мок для чата
    chat = AsyncMock(spec=Chat)
    chat.type = "private"

    # Создаем мок для сообщения
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.answer = AsyncMock()
    
    # Мокаем клавиатуру подписки
    keyboard = {"inline_keyboard": []}
    async def mock_get_keyboard():
        return keyboard
        
    with patch('handlers.personal_actions.get_subscription_keyboard', mock_get_keyboard):
        await cmd_start(message)
    
    # Проверяем, что ответ был отправлен
    message.answer.assert_called_once()
    # Проверяем, что в ответе есть клавиатура
    assert message.answer.call_args[1]["reply_markup"] == keyboard

@pytest.mark.asyncio
async def test_cmd_help():
    """Test help command handler"""
    # Создаем мок для пользователя
    user = AsyncMock(spec=User)
    user.id = 123456
    user.username = "test_user"

    # Создаем мок для сообщения
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    
    await cmd_help(message)
    
    # Проверяем, что ответ был отправлен
    message.answer.assert_called_once()

@pytest.mark.asyncio
async def test_cmd_language():
    """Test language command handler"""
    # Создаем мок для пользователя
    user = AsyncMock(spec=User)
    user.id = 123456
    user.username = "test_user"

    # Создаем мок для сообщения
    message = AsyncMock(spec=Message)
    message.from_user = user
    message.answer = AsyncMock()
    
    # Мокаем клавиатуру подписки
    keyboard = {"inline_keyboard": []}
    async def mock_get_keyboard():
        return keyboard
        
    with patch('handlers.personal_actions.get_subscription_keyboard', mock_get_keyboard):
        await cmd_language(message)
    
    # Проверяем, что ответ был отправлен с клавиатурой
    message.answer.assert_called_once()
    assert message.answer.call_args[1]["reply_markup"] == keyboard

@pytest.mark.asyncio
@patch('handlers.personal_actions.check_subscription')
@patch('filters.is_subscribed.IsSubscribedFilter.__call__')
async def test_check_subscription_callback(mock_is_subscribed, mock_check_subscription):
    """Test subscription check callback handler"""
    # Настраиваем мок для проверки подписки
    mock_is_subscribed.return_value = True
    mock_check_subscription.return_value = lambda x: x
    
    # Создаем мок для пользователя
    user = AsyncMock(spec=User)
    user.id = 123456
    user.username = "test_user"

    # Создаем мок для callback
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = user
    callback.answer = AsyncMock()
    
    await check_subscription_callback(callback)
    
    # Проверяем, что ответ на callback был отправлен
    callback.answer.assert_called_once()