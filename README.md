# АэроТрастТехникс Система доверительных сообщений

MVP системы доверенных сообщений:
- Telegram bot (aiogram 3);
- Backend API (FastAPI);
- PostgreSQL + SQLAlchemy 2 + Alembic;
- Redis (FSM + rate limiting);
- локальное хранение вложений;
- Admin UI (React + Vite).

## Что уже реализовано
- bot flow: onboarding, invite code, report submission, attachments, confirmation;
- rate limiting в bot middleware;
- admin API: auth, reports list/detail, status update, analytics, audit logs;
- RBAC (`admin`, `resolver`);
- admin UI: login/logout + вкладки `Reports`, `Analytics`, `Audit Logs`.

## Структура
```text
backend/   API, bot, ORM, migrations, tests
admin/     web admin (React + Vite)
infra/     infra configs/scripts
docs/      source-of-truth документы
```

## Предварительные требования
1. Docker Desktop запущен.
2. Порт `8000` и `5173` свободны.
3. Telegram token для полного bot e2e (`TELEGRAM_BOT_TOKEN`).

## Развертывание MVP с нуля (Docker)
1. Создать `.env`:
```powershell
Copy-Item .env.example .env
```

2. Заполнить минимум:
```env
TELEGRAM_BOT_TOKEN=<real_token>
ADMIN_JWT_SECRET=<strong-secret>
POSTGRES_PASSWORD=<strong-password>
```

3. Поднять сервисы:
```powershell
docker compose up -d --build
```

4. Применить миграции:
```powershell
docker compose exec backend alembic upgrade head
```

5. Проверить доступность:
```powershell
curl http://localhost:8000/healthz
curl http://localhost:5173
```

6. Создать invite code:
```powershell
docker compose exec postgres psql -U aerotrust -d aerotrust -c "INSERT INTO invite_codes (code, is_active, max_uses, used_count) VALUES ('SAFE-REPORT', true, 100, 0) ON CONFLICT DO NOTHING;"
```

7. Создать admin пользователя:
```powershell
docker compose exec backend create-admin-user --email admin --password AdminPass123! --role admin
```

8. (Опционально) resolver:
```powershell
docker compose exec backend create-admin-user --email resolver@example.com --password ResolverPass123! --role resolver --zone process
```

## Деплой на VPS (production compose)
1. Скопировать проект на сервер и перейти в корень репозитория.

2. Подготовить production env:
```bash
cp .env.production.example .env
```

3. Заполнить обязательные переменные в `.env`:
```env
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://aerotrust:<strong-password>@postgres:5432/aerotrust
ADMIN_JWT_SECRET=<strong-random-secret>
TELEGRAM_BOT_TOKEN=<real-token>
ADMIN_HOST_PORT=80
```

4. Запустить деплой:
```bash
bash infra/scripts/deploy_vps.sh
```

5. Создать admin пользователя (один раз):
```bash
docker compose -f docker-compose.prod.yml exec backend create-admin-user --email admin --password '<strong-password>' --role admin
```

6. Создать invite code (один раз):
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U aerotrust -d aerotrust -c "INSERT INTO invite_codes (code, is_active, max_uses, used_count) VALUES ('SAFE-REPORT', true, 100, 0) ON CONFLICT DO NOTHING;"
```

7. Проверить доступность:
```bash
curl http://<server-ip>:<ADMIN_HOST_PORT>/healthz
```

8. Операционные команды:
```bash
# Перезапуск всех сервисов
docker compose -f docker-compose.prod.yml restart

# Статус
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f bot
docker compose -f docker-compose.prod.yml logs -f admin

# Остановка
docker compose -f docker-compose.prod.yml down
```

## Тесты и проверки стабилизации

### Frontend build
```powershell
cd admin
npm install
npm run build
cd ..
```

### Backend unit + integration tests (Python 3.12 в контейнере)
Примечание: runtime image не содержит `tests/`, поэтому тесты запускаются через bind-mount backend каталога.

```powershell
$backendPath = (Resolve-Path .\backend).Path -replace '\\','/'
docker compose run --rm -v "${backendPath}:/app" -e TEST_DATABASE_URL=postgresql+asyncpg://aerotrust:aerotrust@postgres:5432/aerotrust_test backend sh -lc "pip install --no-cache-dir '.[dev]' && pytest -q"
```

## Smoke test сценарий полного MVP

### 1) Bot flow
1. Открыть бота и отправить `/start`.
2. Ввести `SAFE-REPORT`.
3. Пройти сценарий `Отправить сообщение` (режим, категория, текст, вложение, подтверждение).
4. Проверить, что бот вернул `Сообщение принято` и `public_number` формата `AT-...`.

### 2) Admin API
```powershell
$body = '{"email":"admin","password":"AdminPass123!"}'
$token = (Invoke-RestMethod -Method Post -Uri http://localhost:8000/admin/auth/login -ContentType 'application/json' -Body $body).access_token
$headers = @{ Authorization = "Bearer $token" }

Invoke-RestMethod -Method Get -Uri "http://localhost:8000/admin/reports?page=1&page_size=20" -Headers $headers
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/admin/analytics/overview" -Headers $headers
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/admin/audit-logs?page=1&page_size=20" -Headers $headers
```

### 3) Admin UI (E2E)
1. Открыть `http://localhost:5173`.
2. Login: `admin` / `AdminPass123!`.
3. `Reports`: открыть карточку report и сменить статус.
4. `Analytics`: проверить overview + dynamics (`day`/`week`).
5. `Audit Logs`: убедиться, что появляются `report_viewed` / `status_changed`.

### 4) Проверка анонимности
1. В API для анонимного report поле `author` должно быть `null` в list и detail.
2. В UI для такого report отображается только метка `anonymous` без `technical_id`/`telegram_username`.

## Полезные команды
```powershell
# Статус сервисов
docker compose ps

# Логи
docker compose logs backend --tail=100
docker compose logs admin --tail=100

docker compose logs bot --tail=100

# Остановка
docker compose down
```

## Known limitations
- В локальном `docker-compose.yml` admin работает как Vite dev server.
- Для VPS используется `docker-compose.prod.yml` с production static build + nginx.
- E2E UI-проверка требует ручного открытия браузера (в CI не автоматизирована).
- Для полного bot smoke обязателен валидный Telegram token.
- Runtime backend image не включает dev-зависимости и тесты (покрывается bind-mount командой выше).
