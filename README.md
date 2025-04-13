# Проект Foodgram "Продуктовый помощник"

## Описание

Foodgram — это веб-приложение, где пользователи могут публиковать свои рецепты, подписываться на любимых авторов, добавлять рецепты в избранное и формировать список покупок для выбранных блюд.

Проект реализован с использованием Django REST Framework для бэкенда и React для фронтенда.

## Стек технологий

*   **Бэкенд:** Python 3.11, Django 5.x, Django REST Framework (DRF)
*   **База данных:** PostgreSQL 14
*   **Веб-сервер:** Nginx
*   **WSGI-сервер:** Gunicorn
*   **Контейнеризация:** Docker, Docker Compose
*   **Фронтенд:** React (предоставлен готовый)
*   **CI:** GitHub Actions

## Основные возможности

*   Регистрация и аутентификация пользователей (Token Authentication).
*   Просмотр, создание, редактирование, удаление рецептов.
*   Фильтрация рецептов по автору, избранному, списку покупок.
*   Добавление рецептов в избранное.
*   Создание списка покупок с возможностью скачивания суммированного списка ингредиентов в формате `.txt`.
*   Подписка на других пользователей.
*   Просмотр профилей пользователей и авторов.
*   Загрузка и удаление аватара пользователя через API.
*   Админ-панель Django с поиском и управлением моделями.
*   Документация API (ReDoc).

## Установка и запуск (Docker Compose)

**Требования:**

*   Установленный и запущенный Docker Desktop (или Docker Engine + Docker Compose).

**Инструкции:**

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/klinstone/foodgram-st.git
    cd foodgram-st
    ```

2.  **Создайте файл `.env` для бэкенда:**
    В директории `backend/` создайте файл `.env` и заполните его по следующему образцу:
    ```dotenv
    # backend/.env

    # Django settings
    SECRET_KEY='your_django_secret_key'
    DEBUG=False
    ALLOWED_HOSTS=localhost,127.0.0.1

    # PostgreSQL settings (должны совпадать с infra/.env)
    POSTGRES_DB=foodgram_db
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD='your_db_password'
    DB_HOST=db
    DB_PORT=5432
    ```
    *(Замените значения-заглушки на ваши реальные данные)*.

3.  **Создайте файл `.env` для инфраструктуры:**
    В директории `infra/` создайте файл `.env` и заполните его переменными для базы данных:
    ```dotenv
    # infra/.env
    POSTGRES_DB=foodgram_db
    POSTGRES_USER=foodgram_user
    POSTGRES_PASSWORD='your_db_password'
    ```
    *(Замените значение-заглушку на ваш реальный пароль)*.

4.  **Соберите и запустите контейнеры:**
    Находясь в корневой директории проекта (`foodgram-st`), выполните команду:
    ```bash
    docker compose -f infra/docker-compose.yml up --build
    ```
    *(При первом запуске или после изменений в коде используйте `--build`. Для последующих запусков достаточно `up`)*.

5.  **Выполните первоначальную настройку бэкенда (в отдельном терминале):**
    *   Применение миграций (выполняется автоматически при запуске, но для информации):
        ```bash
        docker compose -f infra/docker-compose.yml exec backend python manage.py migrate
        ```
    *   Создание суперпользователя Django:
        ```bash
        docker compose -f infra/docker-compose.yml exec backend python manage.py createsuperuser
        ```
    *   Загрузка ингредиентов в базу данных:
        ```bash
        docker compose -f infra/docker-compose.yml exec backend python manage.py load_ingredients
        ```
    *   Сбор статики (выполняется автоматически при запуске, но для информации):
        ```bash
        docker compose -f infra/docker-compose.yml exec backend python manage.py collectstatic --noinput
        ```

6.  **Доступ к приложению:**
    *   Сайт: [http://localhost](http://localhost)
    *   Админ-панель: [http://localhost/admin/](http://localhost/admin/)
    *   Документация API: [http://localhost/api/docs/](http://localhost/api/docs/)

## Образ Docker Hub

Образ бэкенда доступен на Docker Hub:
[https://hub.docker.com/r/klinstone/foodgram-st](https://hub.docker.com/r/klinstone/foodgram-st)

## Статус CI

[![Foodgram Backend CI](https://github.com/klinstone/foodgram-st/actions/workflows/main.yml/badge.svg)](https://github.com/klinstone/foodgram-st/actions/workflows/main.yml)

## Автор

*   [Ефим Черных](https://github.com/klinstone)