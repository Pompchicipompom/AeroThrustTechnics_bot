# Резервное копирование и восстановление

## Что необходимо сохранять

| Объект | Содержание |
|--------|------------|
| Volume `aerotrust_postgres_data` | Обращения, пользователи, invite-коды, audit logs |
| Volume `aerotrust_uploads_data` | Файловые вложения |
| Volume `aerotrust_redis_data` | FSM / rate limit (некритично; можно не переносить) |

Перед обновлением версии и перед необратимыми операциями с volumes рекомендуется выполнить backup.

## Резервное копирование PostgreSQL

Скрипт:

```bash
bash infra/scripts/backup_postgres.sh
```

Эквивалент вручную:

```bash
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aerotrust aerotrust | gzip > "backups/aerotrust_$(date +%Y%m%d_%H%M%S).sql.gz"
```

## Резервное копирование вложений

```bash
bash infra/scripts/backup_uploads.sh
```

Скрипт сохраняет архив содержимого `/app/uploads` из контейнера `backend`.

## Где хранить резервные копии

Рекомендуется:

- каталог вне Docker volumes приложения (например, `backups/` на хосте);
- копирование на отдельное хранилище / объектное хранилище по политике организации;
- ограничение прав доступа к файлам backup.

Каталог `backups/` в git не включается.

## Восстановление PostgreSQL

Операция перезаписывает данные в базе. Перед восстановлением рекомендуется остановить запись (`backend` / `bot`) или весь стек.

```bash
gunzip -c backups/aerotrust_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aerotrust -d aerotrust
```

После восстановления:

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/healthz
```

## Восстановление вложений

Пример распаковки архива в volume через временный контейнер или копирование в смонтированный каталог зависит от выбранного способа backup.  
При использовании `backup_uploads.sh` архив содержит каталог `uploads/`; его содержимое должно оказаться в `/app/uploads` контейнеров `backend` и `bot` (общий volume `uploads_data`).

Пример восстановления через контейнер `backend`:

```bash
gunzip -c backups/uploads_YYYYMMDD_HHMMSS.tar.gz | \
  docker compose -f docker-compose.prod.yml exec -T backend \
  tar -C /app -xzf -
```

(точный формат имени файла зависит от времени создания backup).

## Перенос на другой сервер

1. Выполнить backup PostgreSQL и uploads на исходном сервере
2. Развернуть проект на новом сервере по `README_DEPLOY.md`
3. Восстановить dump в PostgreSQL
4. Восстановить uploads в volume
5. Проверить `/healthz`, админку и наличие обращений

## Запрещённые действия

- `docker compose down -v` в production без предварительного backup и явной необходимости
- Хранение единственной копии backup на том же диске без внешней репликации (по возможности)
