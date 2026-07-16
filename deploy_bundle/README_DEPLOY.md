# Инструкция по развёртыванию

## Назначение системы

Система доверительных (в том числе анонимных) обращений:

- Telegram-бот для подачи обращений сотрудниками;
- Backend API (FastAPI) для администрирования;
- веб-админка для просмотра обращений, аналитики и журнала действий;
- PostgreSQL для хранения данных;
- Redis для FSM бота и ограничения частоты запросов;
- локальное хранение файловых вложений.

Промышленный запуск выполняется через Docker Compose (`docker-compose.prod.yml`).

## Состав сервисов

| Сервис | Назначение |
|--------|------------|
| `postgres` | PostgreSQL 16 — обращения, пользователи, учётные записи админки |
| `redis` | Redis 7 — FSM бота, rate limiting |
| `backend` | FastAPI — admin API и `/healthz` |
| `bot` | Telegram-бот (aiogram, long polling) |
| `admin` | Статическая админ-панель и Nginx (reverse proxy) |

Публичная точка входа: контейнер `admin` на порту `ADMIN_HOST_PORT` (по умолчанию `80`).

Nginx отдаёт интерфейс `/admin/`, проксирует API `/admin/*` и `/healthz` на `backend`.  
Порты PostgreSQL и Redis наружу не публикуются.

Связанные документы:

- `SERVER_REQUIREMENTS.md` — требования к серверу
- `ENVIRONMENT_VARIABLES.md` — переменные окружения
- `SECRETS_REQUIRED.md` — секретные данные
- `BACKUP_AND_RESTORE.md` — резервное копирование и восстановление
- `UPDATE_PROCEDURE.md` — порядок обновления
- `PROD_CHECKLIST.md` — чеклист перед запуском в production
- `AUDIT_REPORT.md` — отчёт о технической проверке
- `VERSION_REPORT.md` — версии и зависимости

## Требования к серверу

Кратко: Linux с Docker Engine и Docker Compose v2, исходящий доступ к `https://api.telegram.org`.  
Подробности — в `SERVER_REQUIREMENTS.md`.

## Подготовка переменных окружения

```bash
cp .env.production.example .env
nano .env
```

Необходимо заменить плейсхолдеры как минимум для:

- `POSTGRES_PASSWORD` (тот же пароль в `DATABASE_URL`)
- `ADMIN_JWT_SECRET`
- `TELEGRAM_BOT_TOKEN`

Production-файл `.env` должен храниться только на сервере и не попадать в git.  
Описание переменных: `ENVIRONMENT_VARIABLES.md`.  
Список секретных данных: `SECRETS_REQUIRED.md`.

## Запуск через Docker Compose

Из корня репозитория:

```bash
bash infra/scripts/deploy_vps.sh
```

Скрипт выполняет сборку образов, запуск `postgres`/`redis`, применение миграций и запуск `backend`/`bot`/`admin`.

Ручной вариант:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d backend bot admin
```

## Применение миграций

```bash
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
```

Миграции также выполняются в составе `infra/scripts/deploy_vps.sh`.

## Первичная настройка после первого запуска

Создание учётной записи администратора:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email admin --password '<STRONG_PASSWORD>' --role admin
```

Создание invite-кода:

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U aerotrust -d aerotrust -c \
  "INSERT INTO invite_codes (code, is_active, max_uses, used_count)
   VALUES ('SAFE-REPORT', true, 100, 0)
   ON CONFLICT DO NOTHING;"
```

Опционально — учётная запись с ролью `resolver` (доступ в пределах зоны):

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email resolver@example.com --password '<STRONG_PASSWORD>' \
  --role resolver --zone process
```

## Проверка работоспособности

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/admin/
```

Админ-панель: `http://<адрес-сервера>/admin/`

Базовая проверка бота:

1. Открыть бота в Telegram и отправить `/start`
2. Ввести invite-код
3. Отправить тестовое обращение
4. Убедиться, что обращение отображается в админке

Полный чеклист: `PROD_CHECKLIST.md`.

## Просмотр логов

```bash
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f bot
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f admin
docker compose -f docker-compose.prod.yml ps
```

## Остановка и перезапуск

Перезапуск:

```bash
docker compose -f docker-compose.prod.yml restart
```

Остановка без удаления данных:

```bash
docker compose -f docker-compose.prod.yml down
```

**Не выполнять** в production без явной необходимости:

```bash
docker compose -f docker-compose.prod.yml down -v
```

Флаг `-v` удаляет Docker volumes (база данных и вложения).

## Обновление версии

Порядок описан в `UPDATE_PROCEDURE.md`. Кратко:

```bash
# рекомендуется backup перед обновлением
bash infra/scripts/backup_postgres.sh
bash infra/scripts/backup_uploads.sh

git pull
bash infra/scripts/deploy_vps.sh
```

## Резервное копирование и восстановление

См. `BACKUP_AND_RESTORE.md`.

Необходимо сохранять volumes:

| Volume | Содержимое |
|--------|------------|
| `aerotrust_postgres_data` | Данные PostgreSQL |
| `aerotrust_uploads_data` | Файловые вложения |
| `aerotrust_redis_data` | FSM / rate limit (некритично) |

## HTTPS

Compose публикует HTTP на `ADMIN_HOST_PORT`.  
Рекомендуется TLS-терминация на хосте или балансировщике с проксированием на контейнер `admin`.

## Базовая диагностика ошибок

| Симптом | Действия |
|---------|----------|
| Контейнер не стартует | `docker compose -f docker-compose.prod.yml ps` и `logs` сервиса |
| `/healthz` недоступен | Проверить `backend`, `postgres`, `DATABASE_URL` |
| Бот не отвечает | Проверить `TELEGRAM_BOT_TOKEN`, доступ к `api.telegram.org`, логи `bot` |
| Админка недоступна / белый экран | Проверить `admin`, открытие URL `/admin/`, логи Nginx |
| Ошибка входа в админку | Проверить создание пользователя и `ADMIN_JWT_SECRET` |
| Данные пропали после перезапуска | Убедиться, что не выполнялся `down -v`; проверить volumes |
