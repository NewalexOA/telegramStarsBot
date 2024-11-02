import asyncio
import structlog

from aiogram import Bot
from config_reader import get_config, BotConfig
from dispatcher import get_dispatcher
from logs import init_logging
from utils.db import create_db

async def main():
    """
    Entry point
    """
    init_logging()
    logger = structlog.get_logger()
    
    # Создаем таблицы в БД
    await create_db()
    
    # Initialize bot and dispatcher
    bot_config = get_config(BotConfig, "bot")
    bot = Bot(token=bot_config.token.get_secret_value())
    dp = get_dispatcher()
    
    # Run bot
    await logger.ainfo("Starting the bot...")
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
    