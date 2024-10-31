from aiogram import Dispatcher

from fluent_loader import get_fluent_localization
from middlewares import L10nMiddleware, CheckSubscriptionMiddleware

# init locale
locale = get_fluent_localization()

# init dispatcher
dp = Dispatcher()

# Apply middlewares
dp.message.outer_middleware(L10nMiddleware(locale))
dp.message.middleware(CheckSubscriptionMiddleware(
    excluded_commands=[
        # добавляем новые исключения здесь
        # '/somecommand',
        # '/anothercommand'
    ]
))
dp.pre_checkout_query.outer_middleware(L10nMiddleware(locale))
dp.callback_query.outer_middleware(L10nMiddleware(locale))
