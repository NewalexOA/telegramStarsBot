# Dependency Injection Documentation

## Overview
Папка содержит модули для управления зависимостями приложения, реализуя паттерн Dependency Injection.

## Files Structure

### __init__.py
Пустой файл для обозначения папки как Python-пакета.

### container.py
Основной контейнер зависимостей приложения.

#### Классы:
- `Container`
  - Управляет жизненным циклом всех зависимостей
  - Реализует ленивую инициализацию через @property
  
  #### Атрибуты:
  - `_db: Optional[SQLAlchemyDatabase]` - База данных
  - `_uow: Optional[UnitOfWork]` - Unit of Work
  - `_novel_service: Optional[NovelService]` - Сервис новеллы
  - `_referral_service: Optional[ReferralService]` - Сервис рефералов
  - `_payment_service: Optional[PaymentService]` - Сервис платежей
  - `_admin_service: Optional[AdminService]` - Сервис администрирования

  #### Свойства:
  - `db -> SQLAlchemyDatabase`
    - Возвращает инстанс базы данных
    - Создает при первом обращении
  
  - `uow -> UnitOfWork`
    - Возвращает инстанс Unit of Work
    - Использует session_factory из db
  
  - `novel_service -> NovelService`
    - Возвращает сервис новеллы
    - Инициализируется с uow
  
  - `referral_service -> ReferralService`
    - Возвращает сервис рефералов
    - Инициализируется с uow
  
  - `payment_service -> PaymentService`
    - Возвращает сервис платежей
    - Инициализируется с uow
  
  - `admin_service -> AdminService`
    - Возвращает сервис администрирования
    - Инициализируется с uow

  #### Методы:
  - `setup(dp: Dispatcher) -> None`
    - Регистрирует зависимости в диспетчере
    - Добавляет сервисы в workflow_data
    - Логирует процесс настройки
  
  - `on_startup() -> None`
    - Инициализация при запуске бота
    - Создает таблицы в БД
    - Логирует процесс запуска
  
  - `on_shutdown() -> None`
    - Очистка при завершении работы
    - Закрывает соединение с БД
    - Логирует процесс завершения

## Dependencies
- `aiogram` - Для интеграции с диспетчером
- `structlog` - Логирование
- `database` - Слой работы с БД
- `unit_of_work` - Паттерн Unit of Work
- `services` - Бизнес-логика

## Usage
Контейнер используется в:
- `bot.py` для инициализации приложения
- `dispatcher.py` для регистрации зависимостей
- Всех обработчиках через workflow_data

## Error Handling
- Логирование через structlog
- Корректное закрытие ресурсов
- Обработка ошибок инициализации

## Lifecycle Management
1. Создание контейнера
2. Регистрация в диспетчере
3. Инициализация при запуске
4. Использование в приложении
5. Очистка при завершении 