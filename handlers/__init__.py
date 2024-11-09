from . import admin_actions, personal_actions, referral, novel

# Создаем список роутеров для регистрации
routers = [
    admin_actions.router,
    personal_actions.router,
    referral.router,
    novel.router
]
