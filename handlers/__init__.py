from . import admin_actions, group_events, personal_actions, referral

# Создаем список роутеров для регистрации
routers = [
    admin_actions.router,
    group_events.router,
    personal_actions.router,
    referral.router
]
