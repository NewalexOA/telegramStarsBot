import pytest
from typing import AsyncGenerator
from aiogram import Dispatcher, Bot
from unittest.mock import AsyncMock

from services.novel import NovelService
from services.referral import ReferralService
from services.payment import PaymentService
from services.admin import AdminService

class MockUnitOfWork:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def commit(self):
        pass
    
    async def rollback(self):
        pass

@pytest.fixture
async def mock_uow() -> MockUnitOfWork:
    return MockUnitOfWork()

@pytest.fixture
async def mock_bot() -> AsyncGenerator[Bot, None]:
    bot = AsyncMock(spec=Bot)
    yield bot

@pytest.fixture
async def dp(mock_bot: Bot) -> AsyncGenerator[Dispatcher, None]:
    dp = Dispatcher()
    
    # Создаем моки сервисов
    dp.workflow_data["novel_service"] = AsyncMock(spec=NovelService)
    dp.workflow_data["referral_service"] = AsyncMock(spec=ReferralService)
    dp.workflow_data["payment_service"] = AsyncMock(spec=PaymentService)
    dp.workflow_data["admin_service"] = AsyncMock(spec=AdminService)
    dp.workflow_data["uow"] = MockUnitOfWork()
    
    yield dp