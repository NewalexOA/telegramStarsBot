# Visual Novel Telegram Bot

[English](#visual-novel-telegram-bot) | [Русский](#visual-novel-telegram-bot-1)

Interactive visual novel bot powered by OpenAI GPT-4 with dynamic storyline and character interactions.

## Features

- Interactive storytelling with personalized character names
- Dynamic plot that adapts to player choices
- Visual content with Google Drive image integration
- Message caching system for optimized performance
- Subscription-based access control
- Multi-language support
- Referral system with rewards

## Technical Stack

- Python 3.12+
- aiogram 3.x (Telegram Bot framework)
- OpenAI GPT-4 API
- SQLAlchemy (Database ORM)
- Fluent (Localization)
- aiohttp (Async HTTP client)
- structlog (Logging)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`:
   ```plaintext
   BOT_TOKEN=your_telegram_bot_token
   BOT_OWNERS=[owner_ids]
   BOT_REQUIRED_CHANNEL_ID=channel_id
   BOT_REQUIRED_CHANNEL_INVITE=invite_link
   BOT_OPENAI_API_KEY=your_openai_api_key
   BOT_ASSISTANT_ID=your_assistant_id
   ```

4. Set up the database:
   ```bash
   alembic upgrade head
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## Project Structure

- `handlers/` - Telegram message handlers
  - `novel.py` - Novel game handlers
  - `personal_actions.py` - User commands handlers
  - `referral.py` - Referral system handlers
  
- `models/` - Database models
  - `novel.py` - Novel state and messages models
  - `referral.py` - Referral system models
  
- `services/` - Business logic
  - `novel.py` - Novel game service
  
- `utils/` - Helper functions
  - `openai_helper.py` - OpenAI API integration
  - `image_cache.py` - Image caching system
  - `text_utils.py` - Text processing utilities
  
- `keyboards/` - Telegram keyboard layouts
  - `menu.py` - Main menu keyboard
  - `subscription.py` - Subscription check keyboard

## Novel System

The bot implements a visual novel system with:
- Dynamic storyline based on player choices
- Character interaction and relationship development
- Image integration for visual storytelling
- Progress tracking and state management
- Scene-based narrative structure

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

# Visual Novel Telegram Bot

Интерактивный бот визуальной новеллы, работающий на OpenAI GPT-4 с динамическим сюжетом и взаимодействиями персонажей.

## Особенности

- Интерактивное повествование с персонализированными именами персонажей
- Динамичный сюжет, адаптирующийся к выбору игрока
- Визуальный контент с интеграцией изображений из Google Drive
- Система кэширования сообщений для оптимизации производительности
- Контроль доступа на основе подписки
- Поддержка нескольких языков
- Система рефералов с наградами

## Технический стек

- Python 3.10+
- aiogram 3.x (фреймворк для Telegram Bot)
- OpenAI GPT-4 API
- SQLAlchemy (ORM для базы данных)
- Fluent (локализация)
- aiohttp (асинхронный HTTP клиент)
- structlog (логирование)

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения в `.env`:
   ```plaintext
   BOT_TOKEN=ваш_токен_бота_telegram
   BOT_OWNERS=[идентификаторы_владельцев]
   BOT_REQUIRED_CHANNEL_ID=идентификатор_канала
   BOT_REQUIRED_CHANNEL_INVITE=ссылка_на_приглашение
   BOT_OPENAI_API_KEY=ваш_ключ_api_openai
   BOT_ASSISTANT_ID=ваш_id_ассистента
   ```

4. Настройте базу данных:
   ```bash
   alembic upgrade head
   ```

5. Запустите бота:
   ```bash
   python bot.py
   ```

## Структура проекта

- `handlers/` - Обработчики сообщений Telegram
  - `novel.py` - Обработчики новеллы
  - `personal_actions.py` - Обработчики команд пользователя
  - `referral.py` - Обработчики системы рефералов
  
- `models/` - Модели базы данных
  - `novel.py` - Модели состояния и сообщений новеллы
  - `referral.py` - Модели системы рефералов
  
- `services/` - Бизнес-логика
  - `novel.py` - Сервис новеллы
  
- `utils/` - Вспомогательные функции
  - `openai_helper.py` - Интеграция с OpenAI API
  - `image_cache.py` - Система кэширования изображений
  - `text_utils.py` - Утилиты для обработки текста
  
- `keyboards/` - Макеты клавиатур Telegram
  - `menu.py` - Основная клавиатура меню
  - `subscription.py` - Клавиатура проверки подписки

## Система новеллы

Бот реализует систему визуальной новеллы с:
- Динамичным сюжетом, основанным на выборах игрока
- Взаимодействием персонажей и развитием отношений
- Интеграцией изображений для визуального повествования
- Отслеживанием прогресса и управлением состоянием
- Структурой повествования на основе сцен

## Участие в разработке

1. Сделайте форк репозитория
2. Создайте свою ветку
3. Зафиксируйте ваши изменения
4. Отправьте изменения в ветку
5. Создайте Pull Request

## Лицензия

Этот проект лицензирован под MIT License - смотрите файл LICENSE для подробностей.

---

# Project Documentation

## Overview
Проект представляет собой Telegram бот с функциональностью управления новеллами, платежами, реферальной системой и административными задачами. Архитектура построена по принципам чистой архитектуры, используя паттерны Repository и Dependency Injection.

## Architecture
- **Handlers**: Обработчики сообщений и команд бота.
- **Services**: Бизнес-логика приложения.
- **Repositories**: Работа с данными через паттерн Repository.
- **Database**: Управление базой данных.
- **DI (Dependency Injection)**: Внедрение зависимостей.
- **Filters**: Фильтры для обработки сообщений.
- **Middlewares**: Промежуточные обработчики для проверок и модификаций.

## Services
Сервисы реализованы в папке `services/` и включают следующие компоненты:
- **AdminService**
  - Управление и администрирование бота.
  - Методы: `get_stats`, `get_user_details`, `clear_database`.
- **NovelService**
  - Управление состоянием новелл пользователей.
  - Методы: `start_novel`, `get_novel_state`, `update_novel_state`.
- **ReferralService**
  - Управление реферальной системой.
  - Методы: `create_referral_link`, `process_referral`, `get_user_rewards`.
- **PaymentService**
  - Обработка платежей и управление транзакциями.
  - Методы: `process_payment`, `get_payment_history`, `count_all_payments`, `get_total_payment_amount`.

## Getting Started
1. **Установка зависимостей**:    ```bash
    pip install -r requirements.txt    ```
2. **Настройка конфигурации**:
    - Заполните необходимые параметры в конфигурационных файлах.
3. **Запуск миграций**:    ```bash
    python manage.py migrate    ```
4. **Запуск бота**:    ```bash
    python bot.py    ```

## Features
- Управление новеллами пользователей.
- Обработка платежей и донатов.
- Реферальная система для увеличения аудитории.
- Административные функции для мониторинга и управления.
- Локализация сообщений.
- Проверка подписки пользователей на каналы.

## Error Handling
- Логирование всех операций через `structlog`.
- Обработка исключений в сервисах и обработчиках.
- Корректное управление транзакциями через Unit of Work.

## Contribution
Пожалуйста, следуйте стандартным практикам разработки и тестированию при внесении изменений.

## License
[MIT](LICENSE)
