from sqlalchemy.ext.asyncio import create_async_engine
from models.base import Base
import structlog

async def create_db():
    """Create database tables"""
    logger = structlog.get_logger()
    
    # Создаем движок для SQLite с отключенным эхо
    engine = create_async_engine(
        "sqlite+aiosqlite:///bot.db",
        echo=False  # Отключаем встроенное логирование SQLAlchemy
    )
    
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            await logger.ainfo("Creating database tables")
            await conn.run_sync(Base.metadata.create_all)
            await logger.ainfo("Database tables created successfully")
    except Exception as e:
        await logger.aerror("Error creating database tables", error=str(e))
        raise

async def close_db_connections(engine):
    """Закрытие соединений с базой данных"""
    logger = structlog.get_logger()
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}", exc_info=True)
        raise