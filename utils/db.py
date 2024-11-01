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