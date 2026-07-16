# Скрипты инфраструктуры

## Доступные скрипты

`install_docker_ubuntu.sh`
- Минимальная установка Docker Engine + плагина Docker Compose на Ubuntu.
- Запускать от `root`.

`deploy_vps.sh`
- Проверяет наличие `.env` и Docker Compose.
- Валидирует `docker-compose.prod.yml`.
- Собирает образы, поднимает `postgres`/`redis`.
- Применяет миграции Alembic.
- Поднимает `backend`/`bot`/`admin`.
- Показывает статус и выполняет базовые HTTP-проверки (если установлен `curl`).

`backup_postgres.sh`
- Резервное копирование БД: `pg_dump` → `backups/aerotrust_*.sql.gz`
  (по умолчанию используется `docker-compose.prod.yml`).

`backup_uploads.sh`
- Резервное копирование вложений: tar.gz каталога `/app/uploads` из контейнера `backend`.

## Быстрый запуск

```bash
# в корне проекта на сервере
cp .env.production.example .env
nano .env

bash infra/scripts/deploy_vps.sh
```

Подробные инструкции для IT компании: `deploy_bundle/README_DEPLOY.md`.
