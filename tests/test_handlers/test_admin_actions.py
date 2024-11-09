import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message, User
from aiogram import Dispatcher
from handlers.admin_actions import cmd_stats
from services.admin import AdminService

@pytest.mark.asyncio
class TestAdminActions:
    async def test_cmd_stats(self, dp: Dispatcher):
        # Arrange
        message = AsyncMock(spec=Message)
        message.from_user = AsyncMock(spec=User)
        admin_service = AsyncMock(spec=AdminService)
        admin_service.get_stats.return_value = {
            "total_users": 10,
            "active_novels": 5,
            "completed_novels": 3,
            "total_referrals": 2,
            "active_referrers": 1,
            "total_payments": 4,
            "total_amount": 100
        }
        
        # Act
        await cmd_stats(message, admin_service, AsyncMock())
        
        # Assert
        admin_service.get_stats.assert_called_once()
        message.answer.assert_called_once_with(
            "📊 Статистика бота:\n\n"
            "👥 Всего пользователей: 10\n"
            "📚 Активных новелл: 5\n"
            "✅ Завершенных новелл: 3"
        ) 