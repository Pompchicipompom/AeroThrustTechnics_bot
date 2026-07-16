# Версии и зависимости

Документ фиксирует версии компонентов по состоянию репозитория.  
Фактические версии среды определяются Dockerfile, `docker-compose*.yml` и lock-файлами при сборке образов.

## Приложение

| Компонент | Версия |
|-----------|--------|
| Backend-пакет | `aerotrust-backend` `0.1.0` (`backend/pyproject.toml`) |
| Admin UI | `aerotrust-admin-ui` `0.2.0` (`admin/package.json`) |
| Python | `>=3.12` (образ `python:3.12-slim`) |
| Node (сборка frontend) | `node:20-alpine` |
| Nginx (admin, production) | `nginx:1.27-alpine` |

## Образы инфраструктуры

| Сервис | Образ |
|--------|-------|
| PostgreSQL | `postgres:16-alpine` |
| Redis | `redis:7-alpine` |
| `backend` / `bot` | сборка `./backend` на базе `python:3.12-slim` |
| `admin` (dev) | сборка `./admin` на базе `node:20-alpine` |
| `admin` (prod) | multi-stage: `node:20-alpine` → `nginx:1.27-alpine` (`Dockerfile.prod`) |

## Backend-зависимости (`backend/pyproject.toml`)

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

## Frontend-зависимости (`admin/package.json`)

| Пакет | Ограничение |
|-------|-------------|
| react / react-dom | `^18.3.1` |
| Vite | `^5.4.19` |
| typescript | `^5.8.3` |

Lock-файл: `admin/package-lock.json` (в production-сборке используется `npm ci`).

## Миграции базы данных

| Ревизия | Описание |
|---------|----------|
| `20260421_0001` | Начальная схема |
| `20260421_0002` | Индексы для admin API |

Применение: `alembic upgrade head`.

## Фиксация версий среды

- Базовые образы задаются в Dockerfile и `docker-compose*.yml`
- Python-зависимости — в `backend/pyproject.toml`
- Node-зависимости — в `admin/package.json` и `admin/package-lock.json`
- Точные версии пакетов внутри собранного образа зависят от разрешения диапазонов на момент сборки

Для инвентаризации после сборки:

```bash
docker compose -f docker-compose.prod.yml exec backend pip freeze
```
