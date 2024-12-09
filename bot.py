import asyncio
import logging
import structlog

from aiogram import Bot
from config_reader import bot_config, update_assistant_id
from dispatcher import get_dispatcher
from logs import init_logging
from utils.db import create_db
from utils.openai_helper import create_assistant

# Отключаем лишние логи от библиотек
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.DEBUG)

async def main():
    """
    Entry point
    """
    init_logging()
    logger = structlog.get_logger()
    
    # Создаем таблицы в БД
    await create_db()
    
    # Initialize bot and dispatcher
    bot = Bot(token=bot_config.token.get_secret_value())
    dp = get_dispatcher()
    
    assistant_id = bot_config.assistant_id
    logger.info(f"Assistant ID: {assistant_id}")
    
    # Создаём или проверяем ассистента
    try:
        new_assistant_id = await create_assistant(existing_assistant_id=assistant_id)
        if new_assistant_id != assistant_id:
            logger.info(f"Updating assistant ID: {new_assistant_id}")
            update_assistant_id(new_assistant_id)
    except Exception as e:
        logger.error(f"Critical error with assistant creation/retrieval: {e}")
        raise
    
    # Run bot
    await logger.ainfo("Starting the bot...")
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
    