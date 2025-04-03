# Telegram Uptime Bot

Этот проект представляет собой Telegram бота для мониторинга состояния сервисов через Uptime Kuma. Бот позволяет получать информацию о статусе мониторов, списке мониторов и инцидентах.

## Функциональность

- Получение статуса всех сервисов
- Получение списка мониторов
- Просмотр активных инцидентов
- Проверка доступа на основе списка разрешенных ID чатов

## Установка

### Обычная установка

1. Установите зависимости с помощью Poetry:
   ```bash
   poetry install
   ```

2. Создайте файл `.env` и добавьте необходимые переменные окружения:
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   UPTIME_KUMA_URL=http://ваш_сервер:порт
   UPTIME_KUMA_USERNAME=имя_пользователя
   UPTIME_KUMA_PASSWORD=пароль
   ALLOWED_CHAT_IDS=список_разрешенных_id_чатов_через_запятую
   ```

### Установка с Docker

1. Создайте файл `.env` с теми же переменными окружения, что указаны выше.

2. Соберите Docker образ:
   ```bash
   docker compose build
   ```

## Запуск

### Обычный запуск

Запустите бота с помощью следующей команды:
```bash
poetry run python bot.py
```

Или используя скрипт:
```bash
poetry run bot
```

### Запуск с Docker

```bash
# Запуск
docker compose up -d

# Остановка
docker compose down

# Просмотр логов
docker compose logs -f

# Проверка статуса
docker compose ps
```

## Команды бота

- `/start` или `/help` - Показать справочное сообщение
- `/status` - Получить общий статус всех сервисов
- `/monitors` - Показать список всех мониторов
- `/incidents` - Показать список инцидентов

## Тестирование

Проект включает автоматические тесты для клиента Uptime Kuma и Telegram бота.

### Запуск тестов

Для запуска тестов используйте следующие команды:

```bash
# Запуск всех тестов
poetry run test

# Запуск только тестов клиента Uptime Kuma
poetry run test-client

# Запуск только тестов Telegram бота
poetry run test-bot
```

### Типы тестов

1. **Тесты клиента Uptime Kuma** - проверяют функциональность клиента для работы с API Uptime Kuma
2. **Тесты Telegram бота** - используют моки для тестирования логики обработки команд

## Структура проекта

- `bot.py` - Основной файл бота
- `uptime_kuma_client.py` - Клиент для работы с API Uptime Kuma
- `tests/` - Директория с тестами
  - `test_uptime_kuma_client.py` - Тесты для клиента Uptime Kuma
  - `test_bot.py` - Тесты для Telegram бота
- `Dockerfile` - Файл для сборки Docker образа
- `docker-compose.yaml` - Файл конфигурации Docker Compose

## Используемые технологии

- Python
- aiogram 3.19+
- aiohttp
- python-dotenv
- uptime-kuma-api
- Poetry (управление зависимостями)
- pytest (тестирование)
- Docker (контейнеризация)

## Деплой на сервер

Для деплоя бота на сервер:

1. Клонируйте репозиторий на сервер:
   ```bash
   git clone https://github.com/ваш-пользователь/telegram-uptime-bot.git
   cd telegram-uptime-bot
   ```

2. Создайте файл `.env` с необходимыми переменными окружения.

3. Запустите бота с помощью Docker Compose:
   ```bash
   docker compose build
   docker compose up -d
   ```

4. Настройте автозапуск контейнера при перезагрузке сервера:
   ```bash
   # Уже настроено в docker-compose.yaml с опцией restart: unless-stopped
   ```

## Лицензия

Этот проект лицензирован под MIT License. 