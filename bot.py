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
    
    # Создаём ассистента при первом запуске
    if not assistant_id:
        assistant_id = await create_assistant()
        logger.info(f"Created new assistant with ID: {assistant_id}")
        update_assistant_id(assistant_id)
    
    # Run bot
    await logger.ainfo("Starting the bot...")
    await dp.start_polling(bot, skip_updates=False)

if __name__ == "__main__":
    asyncio.run(main())
    