# Repositories Documentation

## Overview
Папка содержит репозитории для работы с моделями данных, реализуя паттерн Repository для изоляции бизнес-логики от деталей хранения данных.

## Files Structure

### __init__.py
Пустой файл, необходим для корректной работы пакета.

### base.py
Базовый класс для всех репозиториев.

#### Классы:
- `BaseRepository[ModelType](ABC)`
  - Абстрактный базовый класс для всех репозиториев
  - Параметры:
    - `ModelType` - Тип модели данных
  - Методы:
    - `__init__(session: AsyncSession)` - Инициализация с сессией БД
    - `get_model() -> type[ModelType]` - Абстрактный метод для получения класса модели
    - `get(id: int) -> Optional[ModelType]` - Получение записи по ID
    - `add(model: ModelType) -> ModelType` - Добавление новой записи
    - `delete(model: ModelType) -> None` - Удаление записи
    - `update(model: ModelType) -> ModelType` - Обновление записи

### novel.py
Репозиторий для работы с новеллами.

#### Классы:
- `NovelRepository(BaseRepository[NovelState])`
  - Методы:
    - `get_model() -> type[NovelState]` - Возвращает класс NovelState
    - `get_by_user_id(user_id: int) -> Optional[NovelState]` - Получение состояния новеллы пользователя
    - `get_active_novels() -> List[NovelState]` - Получение всех активных новелл
    - `get_stats() -> tuple[int, int, int]` - Получение статистики (всего/активных/завершенных)

### payment.py
Репозиторий для работы с платежами.

#### Классы:
- `PaymentRepository(BaseRepository[Payment])`
  - Методы:
    - `get_model() -> type[Payment]` - Возвращает класс Payment
    - `get_by_user_id(user_id: int) -> List[Payment]` - Получение платежей пользователя
    - `get_pending() -> List[Payment]` - Получение ожидающих платежей
    - `get_stats() -> tuple[int, int]` - Получение статистики (всего/сумма)

### referral.py
Репозиторий для работы с реферальной системой.

#### Классы:
- `ReferralRepository(BaseRepository[ReferralLink])`
  - Методы:
    - `get_model() -> type[ReferralLink]` - Возвращает класс ReferralLink
    - `get_by_user_id(user_id: int) -> Optional[ReferralLink]` - Получение реф. ссылки пользователя
    - `get_by_code(code: str) -> Optional[ReferralLink]` - Поиск ссылки по коду
    - `get_referrals(user_id: int) -> List[Referral]` - Получение рефералов пользователя
    - `get_stats() -> tuple[int, int]` - Получение статистики (ссылок/рефералов)

## Integration Points
- `services/` - Использование через Unit of Work
- `models/` - Работа с моделями данных
- `database/` - Доступ к БД через сессии
- `handlers/` - Косвенное использование через сервисы

## Dependencies
- `sqlalchemy` - ORM и типы
- `structlog` - Логирование
- `typing` - Типизация
- `models/` - Модели данных

## Error Handling
- Логирование через structlog
- Обработка ошибок БД
- Возврат None при отсутствии данных
- Корректная обработка транзакций

## Features
- Типизация через generics
- Единый интерфейс CRUD
- Изоляция SQL-запросов
- Поддержка статистики
- Асинхронная работа
