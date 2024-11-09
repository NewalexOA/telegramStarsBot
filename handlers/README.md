# Handlers Documentation

## Overview
Папка содержит обработчики сообщений и команд Telegram бота, организованные по функциональным модулям.

## Files Structure

### __init__.py
Инициализация и регистрация роутеров:
- Импорт всех модулей обработчиков
- Список роутеров для регистрации в диспетчере:
  - admin_actions.router
  - personal_actions.router
  - referral.router
  - novel.router

### admin_actions.py
Обработчики административных действий.

#### Роутер:
- `router = Router(name="admin")`
  - Фильтры: `IsAdminFilter(is_admin=True)`

#### Функции:
- `cmd_stats(message, admin_service, l10n)`
  - Получение общей статистики бота
  - Показывает количество пользователей и новелл
  
- `menu_clear_db(message, admin_service, l10n)`
  - Запрос на очистку базы данных
  - Показывает кнопки подтверждения
  
- `clear_db_confirm(callback, admin_service, l10n)`
  - Подтверждение и выполнение очистки БД
  - Логирует действие администратора
  
- `clear_db_cancel(callback, l10n)`
  - Отмена очистки БД

### base.py
Базовые классы и миксины.

#### Классы:
- `PermissionMixin`
  - `check_permissions(message) -> tuple[bool, bool]`
    - Проверка прав админа/владельца
  - `check_subscription(message, l10n) -> bool`
    - Проверка подписки на канал

### novel.py
Обработчики для работы с новеллой.

#### Константы:
- `PRIORITIES` - Приоритеты обработки сообщений
- `MENU_COMMANDS` - Список команд меню

#### Функции:
- `start_novel_common(message, novel_service, l10n)`
  - Общая логика запуска новеллы
  - Создание состояния и первое сообщение
  
- `continue_novel(message, novel_service, l10n)`
  - Продолжение существующей новеллы
  - Показ последнего сообщения
  
- `handle_menu_command(message, novel_service, l10n)`
  - Обработка команд меню
  - Проверка прав для админских команд
  
- `handle_text(message, novel_service)`
  - Обработка текстовых сообщений в новелле

### payments.py
Обработчики платежей и донатов.

#### Константы:
- `RESTART_COST = 10` - Стоимость рестарта новеллы

#### Функции:
- `send_donate_invoice(message, amount, l10n)`
  - Отправка счета для доната
  
- `process_pre_checkout_query(pre_checkout_query)`
  - Предварительная проверка платежа
  
- `handle_successful_payment(message, novel_service, payment_service, l10n)`
  - Обработка успешного платежа
  
- `send_restart_invoice(message, l10n)`
  - Отправка счета для рестарта новеллы
  
- `cmd_donate(message, command, l10n)`
  - Обработка команды доната

### personal_actions.py
Обработчики персональных действий пользователя.

#### Роутер:
- `router = Router(name="personal_actions")`
  - Фильтры: `ChatTypeFilter(["private"])` - только личные сообщения

#### Функции:
- `cmd_start(message, novel_service, l10n, state)`
  - Обработка команды /start без реферального кода
  - Очистка состояния FSM
  - Проверка прав админа/владельца
  - Проверка состояния новеллы
  - Отправка счета для рестарта если новелла завершена
  - Показ соответствующего меню (админ/пользователь)
  - Проверка подписки для обычных пользователей

- Обработчики меню админа:
  - `menu_stats(message, admin_service, l10n)`
    - Показ общей статистики бота
    - Доступно только админам/владельцам
  - `menu_clear_db(message, l10n)`
    - Запрос подтверждения очистки БД
    - Доступно только админам/владельцам
  - `on_clear_db_confirm(callback, admin_service, l10n, state)`
    - Подтверждение и выполнение очистки БД
    - Очистка состояния FSM
  - `on_clear_db_cancel(callback, l10n)`
    - Отмена очистки БД

- Обработчики платежей:
  - `pre_checkout_query(query, l10n)`
    - Предварительная проверка платежа
  - `on_successful_payment(message, novel_service, payment_service, l10n)`
    - Обработка успешного платежа
    - Различная логика для рестарта и доната

- Обработчики меню новеллы:
  - `menu_novel(message, novel_service, l10n)`
    - Запуск новеллы
    - Проверка подписки
    - Особая логика для админов
  - `menu_continue(message, novel_service, l10n)`
    - Продолжение существующей новеллы
    - Проверка подписки
  - `menu_restart(message, novel_service, l10n)`
    - Рестарт новеллы
    - Особая логика для админов
    - Отправка счета для обычных пользователей

- Обработчики дополнительных функций:
  - `menu_ref_link(message, referral_service, l10n)`
    - Получение реферальной ссылки
    - Проверка подписки
  - `menu_donate(message, l10n)`
    - Показ меню выбора суммы доната
    - Кнопки для разных сумм
  - `menu_help(message, l10n)`
    - Показ справочной информации
  - `on_donate_amount(callback, l10n)`
    - Обработка выбора суммы доната
    - Отправка счета на оплату

#### Особенности:
- Все обработчики используют локализацию (l10n)
- Логирование ошибок через structlog
- Проверка прав для админских функций
- Проверка подписки для обычных пользователей
- Интеграция с различными сервисами:
  - NovelService для работы с новеллой
  - AdminService для админских функций
  - PaymentService для платежей
  - ReferralService для рефералов
- Использование FSM для управления состоянием
- Обработка ошибок с информативными сообщениями

### referral.py
Обработчики реферальной системы.

#### Функции:
- `cmd_ref(message, referral_service, l10n)`
  - Получение реферальной ссылки
  
- `cmd_start_with_ref(message, referral_service, l10n)`
  - Обработка реферального старта
  
- `show_ref_link(message, referral_service, l10n)`
  - Показ реферальной ссылки
  
- `show_stats(message, referral_service, l10n)`
  - Показ статистики рефералов

## Dependencies
- `aiogram` - Фреймворк бота
- `structlog` - Логирование
- `services/` - Бизнес-логика
- `filters/` - Фильтры сообщений
- `keyboards/` - Клавиатуры
- `config_reader` - Конфигурация

## Error Handling
- Логирование через structlog
- Try/except в каждом обработчике
- Информативные сообщения об ошибках
- Откат состояния при ошибках

## State Management
- FSMContext для хранения состояния
- Очистка состояния при необходимости
- Интеграция с сервисами новеллы

## Security
- Проверка прав через фильтры
- Валидация платежей
- Проверка подписки
- Защита админских функций

## Integration Points
- Сервисы для бизнес-логики
- Клавиатуры для UI
- Фильтры для проверок
- Локализация для текстов