from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from handlers import admin_actions, novel, personal_actions, referral
from middlewares.check_subscription import CheckSubscriptionMiddleware
from middlewares.localization import L10nMiddleware
from middlewares.db import DatabaseMiddleware
from fluent_loader import get_fluent_localization

def get_dispatcher() -> Dispatcher:
    """
    Создает и настраивает диспетчер
    """
    # Создаем диспетчер
    dp = Dispatcher(storage=MemoryStorage())
    
    # Создаем движок базы данных
    engine = create_async_engine(
        "sqlite+aiosqlite:///bot.db",
        echo=False
    )
    
    # Создаем фабрику сессий
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    # Регистрируем мидлвари
    dp.message.middleware(DatabaseMiddleware(session_maker))
    dp.callback_query.middleware(DatabaseMiddleware(session_maker))
    
    # Регистрируем локализацию
    i18n_middleware = L10nMiddleware(get_fluent_localization())
    dp.message.outer_middleware(i18n_middleware)
    dp.callback_query.outer_middleware(i18n_middleware)
    dp.pre_checkout_query.outer_middleware(i18n_middleware)
    
    # Регистрируем обработчики в правильном порядке:
    
    # 1. Админские команды (высший приоритет)
    dp.include_router(admin_actions.router)
    
    # 2. Реферальные команды (второй по приоритету)
    dp.include_router(referral.router)
    
    # 3. Проверка подписки
    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())
    
    # 4. Обработчики команд и callback-ов
    dp.include_router(personal_actions.router)
    
    # 5. Обработчик новеллы (самый низкий приоритет)
    dp.include_router(novel.router)
    
    return dp
