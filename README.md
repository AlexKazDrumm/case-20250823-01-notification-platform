# Платформа многоканальных уведомлений

Django-сервис для создания, планирования и доставки уведомлений через Email,
SMS и Telegram.

## Возможности

- один или несколько получателей;
- настраиваемый порядок каналов;
- последовательная доставка с fallback;
- отправка по выбранному каналу;
- история статусов и попыток доставки;
- асинхронные задачи через Celery;
- webhooks провайдеров;
- web-панель, REST API, Swagger и GraphQL;
- mock-режим для локальной разработки.

## Стек

Django 5, Django REST Framework, Celery, Redis, PostgreSQL, Strawberry GraphQL,
drf-spectacular и Docker Compose.

## Запуск

```powershell
Copy-Item .env.example .env
docker compose up --build
```

- web-панель: http://localhost
- Swagger: http://localhost/api/docs/
- GraphQL: http://localhost/graphql

## Локальная разработка

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Для локального запуска без PostgreSQL используется SQLite. Асинхронную доставку
можно заменить синхронной, задав `CELERY_EAGER=1`.

## Документация

Исходные требования приведены в [TASK.md](TASK.md).
