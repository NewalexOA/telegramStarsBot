# Telegram Novel Bot

Интерактивный бот для прохождения новелл с использованием OpenAI Assistant.

## Возможности

### Для пользователей
- 🎮 Интерактивное прохождение новеллы
- 🔄 Возможность рестарта истории
- 💝 Система донатов
- 🔗 Реферальная система
- 📖 Продолжение прерванной истории
- 🌍 Мультиязычность

### Для администраторов
- 📊 Статистика реферальной системы
- 🗑️ Управление базой данных
- 🛠️ Системные команды

## Руководство администратора

### Команды администратора

#### Системные команды
- `/ping` - Проверка работоспособности бота
- `/get_id` - Получение ID пользователя/чата
- `/end_novel` - Принудительное завершение новеллы

#### Статистика
- `📊 Статистика` - Просмотр статистики реферальной системы:
  - Общее количество рефералов
  - Количество уникальных рефереров
  - Топ-5 рефереров

#### Управление базой данных
- `🗑 Очистить базу` - Полная очистка базы данных
  - Требует подтверждения
  - После очистки бот перезапускается

### Приоритеты обработки сообщений

1. Системные команды (100)
2. Административные команды (90)
3. Команды управления (80)
4. Меню и кнопки (70)
5. Обработка текста (60)

### Фильтры и ограничения

- Проверка на администратора
- Проверка на владельца
- Проверка подписки на канал
- Фильтр типа чата (только личные сообщения)

### Логирование

Бот ведет подробное логирование всех действий:
- Создание/завершение новелл
- Обработка сообщений
- Действия администраторов
- Ошибки и исключения

### Безопасность

1. Проверка прав доступа:
   ```python
   is_admin = await IsAdminFilter(is_admin=True)(message)
   is_owner = await IsOwnerFilter(is_owner=True)(message)
   ```

2. Подтверждение опасных операций:
   ```python
   kb = InlineKeyboardBuilder()
   kb.button(text="✅ Да", callback_data="clear_db_confirm")
   kb.button(text="❌ Нет", callback_data="clear_db_cancel")
   ```

### Конфигурация

Настройки бота хранятся в `config.toml`:
- Токен бота
- ID администраторов
- ID обязательного канала
- Токен OpenAI
- ID ассистента OpenAI

### Мониторинг

Рекомендуется следить за:
1. Логами бота
2. Статистикой реферальной системы
3. Нагрузкой на OpenAI API
4. Состоянием базы данных

### Рекомендации

1. Регулярно проверяйте логи на наличие ошибок
2. Делайте бэкапы базы данных перед очисткой
3. Следите за статистикой использования
4. Проверяйте работу реферальной системы
5. Тестируйте новые функции в тестовом окружении

### Устранение неполадок

1. Бот не отвечает:
   - Проверьте `/ping`
   - Проверьте логи
   - Проверьте подключение к OpenAI

2. Ошибки в новелле:
   - Используйте `/end_novel`
   - Проверьте состояние в базе данных
   - Проверьте ответы OpenAI Assistant

3. Проблемы с базой данных:
   - Сделайте бэкап
   - Используйте `🗑 Очистить базу`
   - Проверьте права доступа
