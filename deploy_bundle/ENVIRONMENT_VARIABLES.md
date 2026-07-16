# Переменные окружения

Источник шаблона для промышленной среды: `.env.production.example`.  
Production-конфигурация должна храниться в файле `.env` на сервере и не попадать в git.

## Правила хранения

- Файл `.env` с реальными значениями создаётся на сервере из `.env.production.example`
- Реальные значения не должны храниться в репозитории, общих архивах и документации
- Пароль в `DATABASE_URL` должен совпадать с `POSTGRES_PASSWORD`

## Список переменных

| Переменная | Обязательная | Назначение | Пример (не секрет) |
|------------|--------------|------------|--------------------|
| `APP_ENV` | да | Режим приложения (`prod` отключает OpenAPI/docs) | `prod` |
| `LOG_LEVEL` | нет | Уровень логирования | `INFO` |
| `API_HOST` | нет | Адрес прослушивания API | `0.0.0.0` |
| `API_PORT` | нет | Порт API внутри контейнера | `8000` |
| `POSTGRES_DB` | да | Имя БД PostgreSQL | `aerotrust` |
| `POSTGRES_USER` | да | Пользователь PostgreSQL | `aerotrust` |
| `POSTGRES_PASSWORD` | да | Пароль PostgreSQL | `replace-with-strong-password` |
| `DATABASE_URL` | да | Строка подключения backend/bot | `postgresql+asyncpg://aerotrust:…@postgres:5432/aerotrust` |
| `REDIS_URL` | да | Подключение к Redis | `redis://redis:6379/0` |
| `ADMIN_JWT_SECRET` | да | Секрет подписи JWT админки | `replace-with-strong-random-secret` |
| `ADMIN_JWT_ALGORITHM` | нет | Алгоритм JWT | `HS256` |
| `ADMIN_ACCESS_TOKEN_TTL_MINUTES` | нет | TTL access-токена (минуты) | `480` |
| `ADMIN_PASSWORD_HASH_ITERATIONS` | нет | Итерации PBKDF2 для паролей админки | `390000` |
| `TELEGRAM_BOT_TOKEN` | да | Токен Telegram-бота | `replace-with-real-token` |
| `BOT_POLLING_TIMEOUT` | нет | Таймаут long polling | `30` |
| `BOT_FORCE_IPV4` | нет | Принудительный IPv4 к Telegram API | `true` |
| `BOT_RATE_LIMIT_ENABLED` | нет | Включение rate limit бота | `true` |
| `BOT_RATE_LIMIT_MAX_EVENTS` | нет | Лимит событий в окне | `10` |
| `BOT_RATE_LIMIT_WINDOW_SECONDS` | нет | Окно rate limit (сек) | `10` |
| `BOT_RATE_LIMIT_BLOCK_SECONDS` | нет | Блокировка при превышении (сек) | `30` |
| `UPLOADS_ROOT` | нет | Каталог вложений в контейнере | `/app/uploads` |
| `MAX_REPORT_TEXT_LENGTH` | нет | Максимальная длина текста обращения | `4000` |
| `MAX_ATTACHMENT_SIZE_MB` | нет | Максимальный размер вложения (МБ) | `10` |
| `MAX_ATTACHMENTS_PER_REPORT` | нет | Максимум вложений на обращение | `5` |
| `ALLOWED_DOCUMENT_EXTENSIONS` | нет | Разрешённые расширения файлов | `.pdf,.doc,...` |
| `ALLOWED_DOCUMENT_MIME_TYPES` | нет | Разрешённые MIME-типы | `application/pdf,...` |
| `ADMIN_HOST_PORT` | нет | Порт хоста для Nginx admin | `80` |

## Переменные, не используемые текущим кодом

Следующие имена могут встречаться в устаревших материалах и не применяются:

- `TELEGRAM_WEBHOOK_*` — бот работает через polling
- `SECRET_KEY` — используется `ADMIN_JWT_SECRET`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` в env — учётные записи создаются командой `create-admin-user`

## Связанные документы

- `SECRETS_REQUIRED.md` — перечень секретных данных
- `.env.production.example` — шаблон без реальных секретов
- `.env.example` — шаблон для локальной разработки
