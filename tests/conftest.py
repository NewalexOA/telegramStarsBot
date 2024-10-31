import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import User

from models.base import Base
from models.enums import RewardType
from config_reader import BotConfig, get_config

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create test database engine"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True,
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

@pytest_asyncio.fixture
async def bot():
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
def dp():
    """Create test dispatcher instance"""
    return Dispatcher()

@pytest.fixture
def reward_type():
    """Create test reward type"""
    return RewardType.CHAPTER_UNLOCK