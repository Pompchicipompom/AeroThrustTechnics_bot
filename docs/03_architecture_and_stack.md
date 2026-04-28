# Архитектура и стек

## 1. Подход
Система состоит из двух интерфейсов:
1. **Telegram bot** — входная точка для отправителей
2. **Web admin** — внутренняя панель обработки

## 2. Рекомендуемая архитектура
- `bot-service` — aiogram bot worker
- `api-service` — FastAPI backend
- `admin-ui` — React/Next.js admin panel
- `db` — PostgreSQL
- `redis` — FSM / cache / rate limit
- `nginx` — reverse proxy
- `uploads` — volume для вложений

## 3. Почему так
- отделяется логика бота и admin;
- проще масштабировать;
- удобно деплоить через Docker Compose;
- легко подключать webhook.

## 4. Деплой на одном VPS
Для MVP все компоненты можно держать на одном сервере:
- Nginx
- API
- Bot
- PostgreSQL
- Redis
- Admin UI

## 5. Рекомендации по безопасности
- только env для секретов;
- не коммитить `.env`;
- ограничить внешние порты;
- БД не выставлять наружу;
- использовать HTTPS;
- добавить basic hardening сервера;
- настроить nightly backups;
- минимизировать логи персональных данных.

## 6. Формат разработки
Итерационно:
1. скелет проекта;
2. БД + миграции;
3. invite codes;
4. сценарий отправки сообщения;
5. вложения;
6. админка;
7. аналитика;
8. деплой.

## 7. Что можно отложить
- SSO
- сложную RBAC
- отдельное object storage
- real-time notifications
- ML/NLP классификацию
