# Models Documentation

## Overview
Папка содержит модели данных SQLAlchemy для всех сущностей бота, включая пользователей, новеллу, платежи и реферальную систему.

## Files Structure

### __init__.py
Экспорт всех моделей:

```pythonfrom .novel import NovelState, NovelMessage
from .user import User
from .payment import Payment
from .referral import ReferralLink, Referral, PendingReferral, ReferralReward
```


### base.py
Базовый класс для всех моделей SQLAlchemy.

#### Классы:
- `Base(DeclarativeBase)`
  - Базовый класс для всех ORM моделей
  - Наследуется всеми моделями в папке
  - Обеспечивает единый интерфейс для работы с БД

### enums.py
Перечисления для моделей.

#### Enums:
- `PaymentStatus(Enum)`
  - `PENDING` - Ожидает оплаты
  - `COMPLETED` - Оплачен
  - `FAILED` - Ошибка оплаты

- `PaymentType(Enum)`
  - `RESTART` - Оплата рестарта новеллы
  - `DONATE` - Донат

### novel.py
Модели для работы с новеллой.

#### Классы:
- `NovelState(Base)`
  - Состояние новеллы пользователя
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `user_id: int (FK)` - ID пользователя
    - `current_message_id: int` - ID текущего сообщения
    - `is_completed: bool` - Завершена ли новелла
    - `created_at: datetime` - Дата создания
    - `updated_at: datetime` - Дата обновления
  - Отношения:
    - `user -> User` - Связь с пользователем
    - `current_message -> NovelMessage` - Текущее сообщение

- `NovelMessage(Base)`
  - Сообщение новеллы
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `text: str` - Текст сообщения
    - `image_url: str` - URL изображения
    - `choices: JSON` - Варианты выбора
    - `next_message_id: int` - ID следующего сообщения

### payment.py
Модель платежей.

#### Классы:
- `Payment(Base)`
  - Информация о платеже
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `user_id: int (FK)` - ID пользователя
    - `amount: int` - Сумма платежа
    - `status: PaymentStatus` - Статус платежа
    - `type: PaymentType` - Тип платежа
    - `created_at: datetime` - Дата создания
    - `completed_at: datetime` - Дата завершения
  - Отношения:
    - `user -> User` - Связь с пользователем

### referral.py
Модели реферальной системы.

#### Классы:
- `ReferralLink(Base)`
  - Реферальная ссылка
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `user_id: int (FK)` - ID владельца
    - `code: str` - Уникальный код
    - `created_at: datetime` - Дата создания

- `Referral(Base)`
  - Реферальная связь
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `referrer_id: int (FK)` - ID реферера
    - `referred_id: int (FK)` - ID приглашенного
    - `created_at: datetime` - Дата создания

- `PendingReferral(Base)`
  - Ожидающий реферал
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `user_id: int (FK)` - ID пользователя
    - `ref_code: str` - Код приглашения
    - `created_at: datetime` - Дата создания

- `ReferralReward(Base)`
  - Награда за рефералов
  - Поля:
    - `id: int (PK)` - Идентификатор
    - `user_id: int (FK)` - ID пользователя
    - `amount: int` - Размер награды
    - `created_at: datetime` - Дата создания

### user.py
Модель пользователя.

#### Классы:
- `User(Base)`
  - Информация о пользователе
  - Поля:
    - `id: int (PK)` - Telegram ID
    - `username: str` - Username
    - `full_name: str` - Полное имя
    - `language_code: str` - Код языка
    - `created_at: datetime` - Дата регистрации
  - Отношения:
    - `novel_state -> NovelState` - Состояние новеллы
    - `payments -> List[Payment]` - Платежи
    - `referral_link -> ReferralLink` - Реф. ссылка

## Integration Points
- `repositories/` - Репозитории для работы с моделями
- `services/` - Бизнес-логика
- `handlers/` - Обработчики сообщений
- `unit_of_work/` - Паттерн Unit of Work

## Dependencies
- `sqlalchemy` - ORM
- `datetime` - Работа с датами
- `enum` - Перечисления
- `typing` - Типизация

## Features
- Полная типизация моделей
- Связи между таблицами
- Автоматическое создание схемы
- Поддержка миграций