# Version report (from repository)

Captured during production-readiness audit.

## Application

| Component | Version / pin |
|-----------|----------------|
| Backend package | `aerotrust-backend` `0.1.0` (`backend/pyproject.toml`) |
| Admin UI package | `aerotrust-admin-ui` `0.2.0` (`admin/package.json`) |
| Python | `>=3.12` (runtime image `python:3.12-slim`) |
| Node (build) | `node:20-alpine` |
| Nginx (admin prod) | `nginx:1.27-alpine` |

## Backend dependencies (ranges from `pyproject.toml`)

| Package | Constraint |
|---------|------------|
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

## Admin dependencies (`admin/package.json` / lockfile)

| Package | Constraint |
|---------|------------|
| react / react-dom | `^18.3.1` |
| vite | `^5.4.19` |
| typescript | `^5.8.3` |
| Lockfile | `admin/package-lock.json` present (use `npm ci` in prod build) |

## Infrastructure images (`docker-compose*.yml`)

| Service | Image |
|---------|-------|
| PostgreSQL | `postgres:16-alpine` |
| Redis | `redis:7-alpine` |
| Backend / bot | build `./backend` (`python:3.12-slim`) |
| Admin (dev) | build `./admin` (`node:20-alpine`) |
| Admin (prod) | build `./admin` + `Dockerfile.prod` (`nginx:1.27-alpine`) |

## Migrations

| Revision | File |
|----------|------|
| `20260421_0001` | Initial schema |
| `20260421_0002` | Admin API indexes |

Apply: `alembic upgrade head` (via deploy script or compose).

## Notes

- Exact installed pip/npm versions inside images depend on build time resolution of ranges.
- `TODO: проверить вручную` — after first company build, run `docker compose ... exec backend pip freeze` and attach to ops notes if pin audit is required.
