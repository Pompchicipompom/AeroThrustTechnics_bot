# Отчёт о версиях (по репозиторию)

Сформировано при подготовке к передаче в промышленную среду.

## Приложение

| Компонент | Версия / закрепление |
|-----------|----------------------|
| Backend-пакет | `aerotrust-backend` `0.1.0` (`backend/pyproject.toml`) |
| Admin UI | `aerotrust-admin-ui` `0.2.0` (`admin/package.json`) |
| Python | `>=3.12` (образ `python:3.12-slim`) |
| Node (сборка) | `node:20-alpine` |
| Nginx (admin, prod) | `nginx:1.27-alpine` |

## Зависимости backend (диапазоны из `pyproject.toml`)

| Пакет | Ограничение |
|-------|-------------|
| aiogram | `>=3.7.0,<4.0.0` |
| FastAPI | `>=0.110.0,<1.0.0` |
| SQLAlchemy | `>=2.0.29,<3.0.0` |
| Alembic | `>=1.13.1,<2.0.0` |
| asyncpg | `>=0.29.0,<1.0.0` |
| psycopg | `>=3.1.18,<4.0.0` |
| redis (Python) | `>=5.0.3,<6.0.0` |
| uvicorn | `>=0.29.0,<1.0.0` |
| PyJWT | `>=2.8.0,<3.0.0` |
| pydantic-settings | `>=2.2.1,<3.0.0` |

## Зависимости admin (`admin/package.json` / lockfile)

| Пакет | Ограничение |
|-------|-------------|
| react / react-dom | `^18.3.1` |
| Vite | `^5.4.19` |
| typescript | `^5.8.3` |
| Lockfile | есть `admin/package-lock.json` (в prod-сборке используется `npm ci`) |

## Образы инфраструктуры (`docker-compose*.yml`)

| Сервис | Образ |
|--------|-------|
| PostgreSQL | `postgres:16-alpine` |
| Redis | `redis:7-alpine` |
| backend / bot | сборка `./backend` (`python:3.12-slim`) |
| admin (dev) | сборка `./admin` (`node:20-alpine`) |
| admin (prod) | сборка `./admin` + `Dockerfile.prod` (`nginx:1.27-alpine`) |

## Миграции базы данных

| Ревизия | Описание |
|---------|----------|
| `20260421_0001` | Начальная схема |
| `20260421_0002` | Индексы для admin API |

Применение: `alembic upgrade head` (через скрипт деплоя или Compose).

## Примечания

- Точные версии pip/npm внутри образов зависят от разрешения диапазонов на момент сборки.
- `TODO: проверить вручную` — после первой сборки на сервере компании при необходимости снять `pip freeze` из контейнера `backend` и приложить к эксплуатационным заметкам.
