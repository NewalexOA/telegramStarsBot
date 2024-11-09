# Middlewares Documentation

## Overview
Папка содержит промежуточные обработчики (middleware) для Telegram бота, которые выполняют различные проверки и модификации данных до/после обработки сообщений.

## Files Structure

### __init__.py
Экспорт основных middleware:

```python
from .localization import L10nMiddleware
from .check_subscription import CheckSubscriptionMiddleware
all = [
"L10nMiddleware",
    "CheckSubscriptionMiddleware"
]
```

### check_subscription.py
Middleware для проверки подписки пользователя на обязательные каналы.

#### Классы:
- `CheckSubscriptionMiddleware(BaseMiddleware)`
  - Проверяет подписку пользователя перед обработкой сообщений
  - Параметры:
    - `excluded_commands` - Список команд, для которых проверка не выполняется
  - Методы:
    - `__call__(handler, event, data) -> Any`
      - Проверяет подписку через IsSubscribedFilter
      - Пропускает исключенные команды
      - Отправляет сообщение о необходимости подписки
      - Поддерживает Message и CallbackQuery
  - Особенности:
    - Интеграция с локализацией
    - Использование клавиатуры подписки
    - Детальное логирование

### db.py
Middleware для управления сессиями базы данных.

#### Классы:
- `DatabaseMiddleware(BaseMiddleware)`
  - Управляет сессией SQLAlchemy для каждого запроса
  - Параметры:
    - `session_pool: async_sessionmaker` - Фабрика сессий
  - Методы:
    - `__call__(handler, event, data) -> Any`
      - Создает новую сессию для каждого запроса
      - Добавляет сессию в контекст обработчика
      - Автоматически закрывает сессию после обработки
  - Особенности:
    - Асинхронная работа с БД
    - Автоматическое управление сессиями
    - Обработка ошибок

### localization.py
Middleware для локализации сообщений.

#### Классы:
- `L10nMiddleware(BaseMiddleware)`
  - Добавляет объект локализации в контекст обработчика
  - Параметры:
    - `locale: FluentLocalization` - Объект локализации
  - Методы:
    - `__call__(handler, event, data) -> Any`
      - Добавляет l10n в контекст
      - Передает управление обработчику
  - Особенности:
    - Интеграция с Fluent
    - Поддержка множества языков
    - Простой доступ к переводам

## Dependencies
- `aiogram` - Базовые классы middleware
- `structlog` - Логирование
- `sqlalchemy` - Работа с БД
- `fluent` - Локализация
- `filters` - Фильтры для проверок
- `keyboards` - Клавиатуры UI

## Integration Points
- `handlers/` - Обработчики сообщений
- `database/` - Слой работы с БД
- `services/` - Бизнес-логика
- `filters/` - Фильтры сообщений

## Error Handling
- Логирование через structlog
- Обработка ошибок БД
- Корректное закрытие ресурсов
- Информативные сообщения об ошибках

## Configuration
Middleware настраиваются через:
- BotConfig для параметров подписки
- Fluent для локализации
- SQLAlchemy для БД

## Security
- Проверка подписки
- Безопасная работа с БД
- Валидация данных