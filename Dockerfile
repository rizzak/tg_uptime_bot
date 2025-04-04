FROM python:3.12-slim

WORKDIR /app

# Установка необходимых зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY pyproject.toml ./

# Установка зависимостей напрямую (без использования Poetry)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "aiogram>=3.19.0,<4.0.0" \
    "python-dotenv>=1.1.0,<2.0.0" \
    "aiohttp>=3.8.5,<4.0.0" \
    "uptime-kuma-api>=0.1.0,<1.0.0"

# Копирование всего кода приложения
COPY . .

# Создание директории для логов
RUN mkdir -p logs

# Команда запуска приложения
CMD ["python", "bot.py"] 