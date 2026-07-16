# Отчёт об аудите — AeroThrust Trusted Messages MVP

Дата: 2026-07-16  
Область: локальный репозиторий и готовность Docker-стека к передаче на сервер компании.

## Что проверено

1. Структура проекта (бот, backend, admin, postgres, redis, nginx в admin)
2. Telegram-бот: токен из переменных окружения, обработчики, вложения, ошибки, rate limit
3. Backend/API: проверка работоспособности (`/healthz`), авторизация, RBAC, обработка ошибок, OpenAPI в prod
4. Админка: базовый URL API, пустые состояния, роли на уровне API
5. База данных: PostgreSQL + Alembic + Docker volumes
6. Docker Compose (dev и prod)
7. Сохранность вложений и безопасность путей файлов
8. Секретные данные / `.env*` / `.gitignore`
9. Безопасность: открытые порты, JWT, анонимность в API/UI
10. Логи, скрипты деплоя, пакет документации `deploy_bundle/`
11. Базовая проверка запуска: стек, сохранность данных после перезапуска

## Архитектура (как есть)

```
Telegram ←polling→ bot ──┬──► PostgreSQL (обращения, пользователи, admin_users, …)
                         ├──► Redis (FSM + rate limit)
                         └──► volume uploads
Браузер → admin(nginx|vite) → backend(FastAPI) → PostgreSQL + uploads
```

## Что исправлено

| Проблема | Исправление |
|----------|-------------|
| `PyJWT` использовался в коде, но отсутствовал в `pyproject.toml` | Добавлена явная зависимость |
| Неполный `.env.example` относительно `Settings` | Приведён в соответствие с конфигурацией |
| В dev у Redis не было volume (FSM терялся при recreate) | Добавлен volume `redis_data` в `docker-compose.yml` |
| У backend в dev не было healthcheck; admin не ждал готовности | Healthcheck + условие `service_healthy` |
| В prod были открыты OpenAPI/docs | Отключены при `APP_ENV=prod` / `production` |
| Не было ограничения длины текста обращения | `MAX_REPORT_TEXT_LENGTH` (по умолчанию 4000) |
| Хрупкий hardcoded IP Telegram в prod compose | Удалён; используется `BOT_FORCE_IPV4` |
| Не хватало документации для передачи и handoff секретов | Добавлены `deploy_bundle/` и скрипты backup |
| Пробелы в `.gitignore` | Расширен (`.DS_Store`, `.env.production`, дампы и т.п.) |

## Средний приоритет (задокументировано, код не переписывался)

| Вопрос | Статус |
|--------|--------|
| У анонимных обращений в БД может храниться `author_user_id` (в админке скрыт) | Нужно для сценария «мои обращения» в боте; при прямом доступе к БД возможна деанонимизация — сообщить компании |
| Хелпер `require_roles()` не используется на уровне роутов; зональный RBAC в репозиториях | Для admin/resolver работает; декоратор на роутах — опциональное улучшение |
| Нет CORS middleware | Нормально при same-origin через nginx/vite; нужен только если SPA на другом домене |
| `infra/nginx/default.conf` не подключён к compose | Вспомогательный файл; не удалён |
| `docs/04_env_example.env` устарел | Актуальные шаблоны — `.env.example` и `.env.production.example` |
| Integration-тесты создают схему через `create_all`, не Alembic | Риск расхождения; на деплое миграции всё равно через Alembic |
| Fallback в `deploy_vps.sh` при лимите Docker Hub может пересобрать только backend | Операционный риск, описан |

## Низкий приоритет / оставлено без удаления

| Элемент | Примечание |
|---------|------------|
| `README_FOR_CODEX.md` | Внутренние заметки — оставлен |
| `infra/docker/README.md` | Заглушка |
| Локальный `.env` с токеном | В `.gitignore`; сменить токен при утечке |

Мусорных артефактов сборки (`node_modules`, `__pycache__`, `.DS_Store`, `*.bak`) в чистом клоне не было.  
`docs/*` и `infra/nginx/default.conf` без согласования с компанией не удалять.

## Безопасность

- Admin API требует JWT, кроме `POST /admin/auth/login`
- PostgreSQL и Redis в prod compose наружу не публикуются
- Для `submit_mode=anonymous` автор скрыт в UI/API админки
- Режим «открыто» (не анонимно) показывает technical id и telegram username — это продуктовое поведение
- `TODO: проверить вручную` — TLS, политика паролей, ротация токена, firewall хоста

## Контекст потери данных (эксплуатация)

На прежнем общем VPS volume PostgreSQL AeroThrust уже отсутствовал до этого аудита.  
Текущий пакет снижает риск повторения: именованные volumes, скрипты backup, явный запрет `down -v` в документации.

## Что протестировано (базовая проверка запуска)

| Проверка | Результат |
|----------|-----------|
| `GET /healthz` | OK |
| Admin UI HTTP | 200 на `:5173` |
| Вход в админку + список обращений | OK |
| Polling бота | Работает |
| Данные после `docker compose restart` | OK — тестовая запись в PostgreSQL сохранилась |
| Named volume Redis | Создан (`aerotrust_redis_data`) |
| Unit-тесты (`test_rate_limit`, `test_report_flow_attachments`) | 8 passed |
| `docker-compose.prod.yml config` | OK |
| Сборка prod-образа admin (`Dockerfile.prod`) | OK |
| Скан отслеживаемых файлов на реальный токен из локального `.env` | совпадений нет |
| Полный e2e нового обращения через Telegram UI | `TODO: проверить вручную` |
| Integration pytest (нужна test DB) | `TODO: проверить вручную` |
| HTTPS / домен компании | `TODO: проверить вручную` |

## Добавленные / изменённые файлы (аудит)

### Добавлено

- `deploy_bundle/*`
- `infra/scripts/backup_postgres.sh`
- `infra/scripts/backup_uploads.sh`

### Обновлено

- `backend/pyproject.toml` — PyJWT
- `backend/app/core/config.py` — лимит длины текста
- `backend/app/bot/handlers/report_flow.py` — проверка длины текста
- `backend/app/main.py` — скрытие docs в prod
- `.env.example`, `.env.production.example`
- `.gitignore`
- `docker-compose.yml` — volume Redis + healthcheck
- `docker-compose.prod.yml` — убран hardcoded IP Telegram
- `README.md` — логи, backup, ссылка на `deploy_bundle/`

## Как запускать (кратко)

**Разработка:**

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

**Production:**

```bash
cp .env.production.example .env
bash infra/scripts/deploy_vps.sh
```

## Какие риски остались

1. Нет автоматических ночных backup, пока не настроен cron
2. Анонимность на уровне API/UI, не криптографическая несвязность в БД
3. MVP на одном хосте Docker — без HA/реплик
4. Polling Telegram зависит от исходящей сети
5. Порт админки — HTTP, пока компания не добавит TLS

## Что нужно проверить вручную

- Полный сценарий бота в Telegram end-to-end
- Integration-тесты на стенде компании
- HTTPS, DNS, firewall
- Политика хранения и ротации секретных данных

## Что важно уточнить у компании

- Кто владеет доменом и HTTPS
- Кто хранит токен Telegram и пароли админки
- Срок хранения резервных копий
- Нужен ли режим «открытого» (неанонимного) обращения
- Нужен ли SSH-доступ подрядчику для деплоя
