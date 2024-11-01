from . import admin_actions, group_events, personal_actions, referral

# Создаем список роутеров для регистрации
routers = [
    group_events.router,
    personal_actions.router,
    referral.router,
    admin_actions.router
]
