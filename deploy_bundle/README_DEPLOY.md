# Развёртывание в production / промышленной среде

## Состав проекта

Стек Docker Compose для промышленного запуска:

| Сервис | Назначение |
|--------|------------|
| `postgres` | PostgreSQL 16 — обращения, пользователи, учётки админки |
| `redis` | Redis 7 — FSM бота и ограничение частоты запросов |
| `backend` | API на FastAPI (админка + проверка работоспособности) |
| `bot` | Telegram-бот (aiogram, long polling) |
| `admin` | Статическая админ-панель + Nginx (reverse proxy) |

Публичная точка входа в production: контейнер `admin` (Nginx) на порту `ADMIN_HOST_PORT` (по умолчанию `80`).

Он отдаёт интерфейс `/admin/`, проксирует API `/admin/*` и `/healthz` на `backend`.  
Порты PostgreSQL и Redis **наружу не открываются**.

## 1. Требования к серверу

См. `SERVER_REQUIREMENTS.md`.

## 2. Получение проекта

Предпочтительно — клон приватного репозитория:

```bash
git clone <PRIVATE_REPO_URL> aerotrust
cd aerotrust
```

Либо распаковать архив проекта **без** реального файла `.env`.

## 3. Подготовка переменных окружения (`.env`)

```bash
cp .env.production.example .env
nano .env
```

Обязательно заменить плейсхолдеры:

- `POSTGRES_PASSWORD` (тот же пароль должен быть в `DATABASE_URL`)
- `ADMIN_JWT_SECRET` (длинная случайная строка)
- `TELEGRAM_BOT_TOKEN`

Реальные значения лучше заполнять **прямо на сервере компании**.  
Список секретных данных: `SECRETS_REQUIRED.md`.

## 4. Запуск через Docker Compose

Из корня проекта:

```bash
bash infra/scripts/deploy_vps.sh
```

Или вручную:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d backend bot admin
```

Миграции БД применяются командой `alembic upgrade head` (входит в скрипт деплоя).

## 5. Первичная настройка (один раз)

Создать пользователя админки:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email admin --password '<STRONG_PASSWORD>' --role admin
```

Создать invite-код для сотрудников:

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U aerotrust -d aerotrust -c \
  "INSERT INTO invite_codes (code, is_active, max_uses, used_count)
   VALUES ('SAFE-REPORT', true, 100, 0)
   ON CONFLICT DO NOTHING;"
```

Опционально — пользователь с ролью `resolver` (доступ только к своей зоне):

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email resolver@example.com --password '<STRONG_PASSWORD>' \
  --role resolver --zone process
```

## 6. Проверка работоспособности

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/admin/
```

Админка: `http://<IP-или-домен>/admin/`  
Вход — учётка, созданная на шаге 5.

Базовая проверка запуска бота:

1. Открыть бота в Telegram → `/start`
2. Ввести invite-код
3. Отправить тестовое обращение
4. Убедиться, что оно появилось в админке (вкладка Reports)

## 7. Логи

```bash
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f bot
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f admin
docker compose -f docker-compose.prod.yml ps
```

## 8. Остановка

Остановка без удаления данных:

```bash
docker compose -f docker-compose.prod.yml down
```

**Не использовать** в production:

```bash
docker compose -f docker-compose.prod.yml down -v
```

Флаг `-v` удаляет volumes — пропадут база и вложения.

## 9. Хранение данных (критично)

Именованные volumes Docker:

| Volume | Содержимое |
|--------|------------|
| `aerotrust_postgres_data` | Обращения, пользователи, invite-коды |
| `aerotrust_uploads_data` | Файлы вложений |
| `aerotrust_redis_data` | FSM бота / rate limit (некритично) |

## 10. Резервное копирование и восстановление

```bash
bash infra/scripts/backup_postgres.sh
bash infra/scripts/backup_uploads.sh
```

Восстановление БД (пример):

```bash
# По возможности остановите запись (backend/bot) перед восстановлением
gunzip -c backups/aerotrust_YYYYMMDD.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aerotrust -d aerotrust
```

Дополнительные команды — в `CHECKLIST_BEFORE_PROD.md`.

## 11. Обновление

```bash
git pull
bash infra/scripts/deploy_vps.sh
```

Перед крупным обновлением сделайте backup БД. Миграции выполняются в процессе деплоя.

## 12. HTTPS и домен

Compose отдаёт HTTP на `ADMIN_HOST_PORT`.  
Для промышленной среды рекомендуется TLS-терминация спереди (Nginx / Caddy / Traefik / балансировщик) с проксированием на контейнер `admin`.

`TODO: проверить вручную` — DNS A-запись, сертификат Let's Encrypt, firewall (снаружи только 80/443).

## 13. Типовые ошибки

| Симптом | Что проверить |
|---------|----------------|
| Контейнер не стартует | `docker compose -f docker-compose.prod.yml ps` и `logs` соответствующего сервиса |
| `/healthz` недоступен | Статус `backend` и `postgres`, корректность `DATABASE_URL` |
| Бот не отвечает | `TELEGRAM_BOT_TOKEN`, исходящий доступ к `api.telegram.org`, логи `bot` |
| Админка белый экран | Сборка `admin`, логи Nginx, что открыт именно `/admin/` |
| Ошибка логина в админку | Пользователь создан через `create-admin-user`, верный `ADMIN_JWT_SECRET` |
| Данные пропали после перезапуска | Не использовался ли `down -v`; на месте ли volumes |
