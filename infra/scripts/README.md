# Infra Scripts

## Доступные скрипты

`install_docker_ubuntu.sh`
- Минимальная установка Docker Engine + Docker Compose plugin на Ubuntu.
- Запускать от `root`.

`deploy_vps.sh`
- Проверяет наличие `.env` и Docker Compose.
- Валидирует `docker-compose.prod.yml`.
- Собирает образы, поднимает `postgres`/`redis`.
- Применяет миграции Alembic.
- Поднимает `backend`/`bot`/`admin`.
- Показывает статус и выполняет базовые HTTP-проверки (если установлен `curl`).

## Быстрый запуск

```bash
# в корне проекта на VPS
cp .env.production.example .env
nano .env

bash infra/scripts/deploy_vps.sh
```
