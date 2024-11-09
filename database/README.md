# Database Documentation

## Overview
Папка содержит модули для работы с базой данных, реализующие паттерн Repository через SQLAlchemy.

## Files Structure

### __init__.py
Пустой файл для обозначения папки как Python-пакета.

### base.py
Базовый класс для всех моделей SQLAlchemy.

#### Классы:
- `Base(DeclarativeBase)` 
  - Базовый класс для всех ORM моделей
  - Наследуется от SQLAlchemy DeclarativeBase
  - Используется всеми моделями в models/

### interface.py
Абстрактный интерфейс для работы с базой данных.

#### Классы:
- `DatabaseInterface(ABC)`
  - Определяет базовый интерфейс для работы с БД
  - Методы:
    - `get_session()` - Получение сессии БД
    - `create_all()` - Создание всех таблиц
    - `drop_all()` - Удаление всех таблиц

### sqlalchemy.py
Реализация интерфейса базы данных через SQLAlchemy.

#### Классы:
- `SQLAlchemyDatabase(DatabaseInterface)`
  - Реализует DatabaseInterface
  - Использует SQLite через aiosqlite
  - Методы:
    - `__init__()` 
      - Инициализирует engine и session_factory
      - Использует конфигурацию из BotConfig
    
    - `get_session() -> AsyncGenerator[AsyncSession, None]`
      - Создает и возвращает сессию БД
      - Обрабатывает ошибки и откаты транзакций
      - Автоматически закрывает сессию
    
    - `create_all() -> None`
      - Создает все таблицы в БД
      - Регистрирует модели: NovelState, NovelMessage, User, Payment, ReferralLink
      - Логирует успешное создание
    
    - `drop_all() -> None`
      - Удаляет все таблицы из БД
      - Обрабатывает и логирует ошибки

## Dependencies
- `sqlalchemy` - ORM для работы с БД
- `aiosqlite` - Асинхронный драйвер SQLite
- `structlog` - Логирование
- `config_reader` - Чтение конфигурации
- `models/` - Модели данных

## Usage
База данных используется через:
- Репозитории в repositories/
- Unit of Work в unit_of_work/
- Сервисы в services/

## Error Handling
- Логирование через structlog
- Автоматический откат транзакций при ошибках
- Корректное закрытие сессий
- Обработка ошибок создания/удаления таблиц

## Configuration
Настройки базы данных берутся из:
- BotConfig для параметров подключения
- Моделей для структуры таблиц 