# Порядок обновления

## Подготовка

Перед обновлением необходимо:

1. Убедиться в наличии актуального backup (см. `BACKUP_AND_RESTORE.md`)
2. Зафиксировать текущий статус контейнеров и версию кода

```bash
bash infra/scripts/backup_postgres.sh
bash infra/scripts/backup_uploads.sh
docker compose -f docker-compose.prod.yml ps
git rev-parse --short HEAD
```

## Обновление кода через Git

```bash
cd /path/to/project
git pull
```

При развёртывании из архива — заменить файлы проекта, сохранив серверный `.env` и volumes.

## Пересборка и запуск контейнеров

Рекомендуемый способ:

```bash
bash infra/scripts/deploy_vps.sh
```

Скрипт выполняет сборку, применение миграций и запуск сервисов.

Вручную:

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d postgres redis
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d backend bot admin
```

## Применение миграций

```bash
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
```

## Проверка после обновления

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/admin/
```

Логи:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 backend
docker compose -f docker-compose.prod.yml logs --tail=100 bot
docker compose -f docker-compose.prod.yml logs --tail=100 admin
```

Дополнительно проверить:

- вход в админку;
- наличие ранее созданных обращений;
- отправку тестового сообщения в бот (при необходимости).

## Действия при неуспешном обновлении

1. Зафиксировать ошибки из логов
2. Не выполнять `down -v`
3. При необходимости откатиться на предыдущий git-коммит / предыдущие образы
4. При повреждении данных восстановить PostgreSQL и uploads из backup (`BACKUP_AND_RESTORE.md`)
5. Повторить проверку `/healthz` и админки

Пример отката кода:

```bash
git log --oneline -5
git checkout <previous_commit_sha>
bash infra/scripts/deploy_vps.sh
```

Откат кода не заменяет восстановление БД, если миграции уже изменили схему в несовместимую сторону — в таком случае требуется восстановление из backup, снятого до обновления.
