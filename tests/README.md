# Тесты для Telegram Uptime Bot

В этой директории находятся тесты для проверки функциональности Telegram бота и клиента Uptime Kuma.

## Структура тестов

1. **test_uptime_kuma_client.py** - тесты для клиента Uptime Kuma, работающие с реальным API.
2. **test_bot.py** - тесты для Telegram бота с использованием моков.

## Запуск тестов

Для запуска тестов используйте следующие команды:

```bash
# Запуск всех тестов
poetry run test

# Запуск только тестов клиента Uptime Kuma
poetry run test-client

# Запуск только тестов Telegram бота
poetry run test-bot
```

Или с помощью pytest напрямую:

```bash
# Запуск всех тестов
poetry run pytest

# Запуск тестов с подробным выводом
poetry run pytest -v

# Запуск тестов с определенным маркером
poetry run pytest -m uptime_kuma
poetry run pytest -m telegram

# Запуск конкретного теста
poetry run pytest tests/test_uptime_kuma_client.py::test_get_monitors
```

## Маркеры тестов

В проекте используются следующие маркеры:

- `asyncio` - тесты, использующие асинхронное выполнение
- `uptime_kuma` - тесты, взаимодействующие с API Uptime Kuma
- `telegram` - тесты, связанные с Telegram API

## Важные замечания

1. Тесты клиента Uptime Kuma работают с реальным API, поэтому для их выполнения необходимо иметь активное соединение с сервером Uptime Kuma.
2. Данные для подключения к Uptime Kuma должны быть указаны в файле `.env` в корне проекта.
3. Тесты Telegram бота используют моки и не требуют реального соединения с API Telegram.

## Дополнительные возможности

Для более подробного вывода и анализа тестов доступны следующие опции:

```bash
# Вывод подробной информации о тестах
poetry run pytest -v

# Вывод информации о покрытии кода тестами
poetry run pytest --cov=.

# Генерация отчета о покрытии в формате HTML
poetry run pytest --cov=. --cov-report=html
``` 