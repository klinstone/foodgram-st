
# backend/Dockerfile

# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем переменные окружения, чтобы Python не буферизовал вывод
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем зависимости ОС, необходимые для psycopg2 и Pillow
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Зависимости для psycopg2
    libpq-dev \
    # Зависимости для Pillow
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    # Утилиты
    gettext \
    # Очистка после установки
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
# Используем --no-cache-dir для уменьшения размера образа
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в рабочую директорию
COPY . .

# Открываем порт, на котором будет работать Gunicorn
EXPOSE 8000

# Команда для запуска приложения будет определена в docker-compose.yml
# Она будет включать сбор статики, применение миграций и запуск Gunicorn
# CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]

