from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .base import Base
from .interface import DatabaseInterface
from config_reader import get_config, BotConfig
import structlog

# Импортируем все модели для создания таблиц
from models import NovelState, NovelMessage, User, Payment, ReferralLink

logger = structlog.get_logger()

class SQLAlchemyDatabase(DatabaseInterface):
    """Реализация работы с БД через SQLAlchemy"""
    
    def __init__(self):
        self.bot_config = get_config(BotConfig, "bot")
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///bot.db",
            echo=False
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии базы данных"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Database session error: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_all(self) -> None:
        """Создание всех таблиц"""
        # Явно регистрируем модели в метаданных
        for model in [NovelState, NovelMessage, User, Payment, ReferralLink]:
            if not model.__table__.metadata.tables:
                model.metadata.create_all(self.engine)
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    
    async def drop_all(self) -> None:
        """Удаление всех таблиц"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise