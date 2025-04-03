FROM python:3.12-slim as base

# Установка Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Установка poetry в отдельное окружение
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Добавление poetry в PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Копирование только файлов зависимостей для кэширования слоев
COPY pyproject.toml ./

# Установка зависимостей без виртуального окружения
RUN poetry config virtualenvs.create false --local \
    && poetry install --no-interaction --no-ansi --no-root

# Копирование всего кода приложения
COPY . .

# Команда запуска приложения
CMD ["python", "bot.py"] 