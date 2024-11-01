from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from handlers import routers
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
    
    # Создаем engine и session_maker для БД
    engine = create_async_engine(
        "sqlite+aiosqlite:///bot.db",
        echo=False  # Отключены подробные SQL логи
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    # Получаем локализацию
    l10n = get_fluent_localization()
    
    # Создаем middleware для локализации
    i18n_middleware = L10nMiddleware(l10n)
    
    # Регистрируем мидлвари
    dp.message.middleware(DatabaseMiddleware(session_maker))
    dp.callback_query.middleware(DatabaseMiddleware(session_maker))
    dp.message.middleware(CheckSubscriptionMiddleware())
    dp.callback_query.middleware(CheckSubscriptionMiddleware())
    
    # Добавляем локализацию для всех типов обновлений
    dp.message.outer_middleware(i18n_middleware)
    dp.callback_query.outer_middleware(i18n_middleware)
    dp.pre_checkout_query.outer_middleware(i18n_middleware)
    
    # Регистрируем роутеры
    for router in routers:
        if not router.parent_router:
            dp.include_router(router)
    
    return dp
