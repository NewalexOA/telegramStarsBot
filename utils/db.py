from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from models.base import Base
from models.novel import NovelState, NovelMessage
from models.referral import ReferralLink
import structlog
from sqlalchemy import text

logger = structlog.get_logger()

async def create_db():
    """Create database tables"""
    # Создаем движок для SQLite с отключенным эхо
    engine = create_async_engine(
        "sqlite+aiosqlite:///bot.db",
        echo=False,  # Полностью отключаем встроенное логирование SQLAlchemy
        echo_pool=False  # Отключаем логирование пула соединений
    )
    
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            logger.info("Creating database tables")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Error creating database tables", error=str(e))
        raise
    
    return engine

async def close_db_connections(engine: AsyncEngine):
    """Закрытие соединений с базой данных"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
        raise

async def clear_database(session):
    """
    Очищает все таблицы в базе данных
    """
    logger.info("Starting database cleanup")
    try:
        # Начинаем транзакцию
        async with session.begin():
            # Удаляем данные из всех таблиц
            await session.execute(text("DELETE FROM novel_messages"))
            await session.execute(text("DELETE FROM novel_states"))
            await session.execute(text("DELETE FROM referral_links"))
            
            # Сбрасываем автоинкремент
            await session.execute(text("DELETE FROM sqlite_sequence"))
            
            logger.info("Database tables cleared successfully")
            
            # Проверяем, что таблицы действительно пусты
            for table in [NovelMessage, NovelState, ReferralLink]:
                count = await session.scalar(
                    text(f"SELECT COUNT(*) FROM {table.__tablename__}")
                )
                if count > 0:
                    raise Exception(f"Table {table.__tablename__} still contains {count} records")
                
            logger.info("Database cleanup verification completed")
            
    except Exception as e:
        logger.error(
            "Error during database cleanup",
            error=str(e)
        )
        # Пробуем откатить изменения
        await session.rollback()
        raise