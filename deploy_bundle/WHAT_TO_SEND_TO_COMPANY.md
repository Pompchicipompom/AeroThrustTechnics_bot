# Что передать компании

## Предпочтительный вариант

1. **Доступ к приватному Git-репозиторию** с этим проектом (ветка `main` или release-тег).
2. Папку **`deploy_bundle/`** (уже есть в репозитории) — точка входа для IT.
3. Файл **`.env.production.example`** (шаблон переменных окружения без секретов).
4. Инструкции по запуску: **`deploy_bundle/README_DEPLOY.md`**.
5. Список секретных данных: **`deploy_bundle/SECRETS_REQUIRED.md`**.
6. **Реальные секретные данные** — отдельным защищённым способом (не в репозитории и не в общем архиве).

## Если доступ к git невозможен

Передать архив проекта, в котором есть:

- `backend/`, `admin/`, `infra/`, `docs/`, `deploy_bundle/`
- `docker-compose.yml`, `docker-compose.prod.yml`
- `.env.example`, `.env.production.example`
- `README.md`

**Не включать в архив:**

- реальный `.env` / `.env.production`
- токены, пароли, JWT-секреты
- дампы базы (`*.sql`, `*.sql.gz`)
- каталоги `uploads/`, Docker volumes
- `admin/node_modules/`, `admin/dist/`
- Python venv, `__pycache__`, `.pytest_cache`
- скриншоты с секретами

## Как компания запускает проект

1. Установить Docker и Docker Compose на сервере
2. Следовать `deploy_bundle/README_DEPLOY.md`
3. Создать `.env` из `.env.production.example` и заполнить секретные данные на сервере
4. Пройти `deploy_bundle/CHECKLIST_BEFORE_PROD.md`

## Если компания просит развернуть у себя подрядчиком

Нужно предоставить:

1. SSH-доступ к серверу
2. Пользователя с правами на Docker (`docker` / root)
3. Домен и DNS (желательно, для HTTPS)
4. Токен Telegram-бота и разрешение использовать его на этом сервере

## Чего нельзя передавать в общем письме/архиве

- Реальные файлы `.env`
- Токены Telegram, пароли БД и админки, `ADMIN_JWT_SECRET`
- Дампы базы и содержимое uploads
- Бэкапы чужих проектов с сервера

## С чего начать IT компании

1. `deploy_bundle/SERVER_REQUIREMENTS.md` — требования к серверу  
2. `deploy_bundle/SECRETS_REQUIRED.md` — какие секретные данные запросить  
3. `deploy_bundle/README_DEPLOY.md` — развёртывание  
4. `deploy_bundle/CHECKLIST_BEFORE_PROD.md` — проверка перед промышленным запуском  
5. `deploy_bundle/AUDIT_REPORT.md` — что проверено и какие риски остались  
