import pytest
import pytest_asyncio
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import User, Message, Chat

from models.enums import RewardType
from config_reader import BotConfig, get_config

@pytest.fixture(scope="session")
def event_loop(request: pytest.FixtureRequest) -> Any:
    """Create event loop for tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[Any, None]:
    """Create test database engine"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    yield test_engine
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest_asyncio.fixture
async def bot() -> AsyncGenerator[Bot, None]:
    """Create test bot instance"""
    session = AiohttpSession()
    bot_config = get_config(BotConfig, "bot")
    bot = Bot(bot_config.token.get_secret_value(), session=session)
    
    # Создаем фейковый объект me для тестов
    me = User(id=123456789, is_bot=True, first_name="TestBot", username="test_bot")
    bot.me = me
    
    try:
        yield bot
    finally:
        await bot.session.close()

@pytest.fixture
def dp() -> Dispatcher:
    """Create test dispatcher instance"""
    return Dispatcher()

@pytest.fixture
def reward_type() -> RewardType:
    """Create test reward type"""
    return RewardType.CHAPTER_UNLOCK

@pytest.fixture
async def message() -> Message:
    """Создает тестовое сообщение"""
    return Message(
        message_id=1,
        date=1,
        chat=Chat(id=1, type="private"),
        from_user=User(
            id=1,
            is_bot=False,
            first_name="Test"
        )
    )