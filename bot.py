import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config_reader import get_config, BotConfig
from middlewares.db import DbSessionMiddleware
from middlewares.localization import L10nMiddleware
from handlers import (
    novel, referral, personal_actions
)
from di.container import Container
from fluent_loader import get_fluent_localization

logger = structlog.get_logger()
bot_config = get_config(BotConfig, "bot")

async def main():
    logger.info("Starting bot")
    
    # Инициализация бота и хранилища
    bot = Bot(token=bot_config.token.get_secret_value())
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация контейнера
    container = Container()
    await container.on_startup()
    
    # Регистрация зависимостей
    container.setup(dp)
    
    # Регистрация middleware
    dp.update.middleware(DbSessionMiddleware(container.db.session_factory))
    
    # Регистрация локализации
    i18n_middleware = L10nMiddleware(get_fluent_localization())
    dp.message.outer_middleware(i18n_middleware)
    dp.callback_query.outer_middleware(i18n_middleware)
    
    # Регистрация роутеров
    dp.include_router(novel.router)
    dp.include_router(referral.router)
    dp.include_router(personal_actions.router)
    
    try:
        logger.info("Starting polling")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down")
        await container.on_shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
    