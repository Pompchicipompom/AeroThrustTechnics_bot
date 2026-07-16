# Production deployment guide

## Overview

Services (Docker Compose production stack):

| Service | Role |
|---------|------|
| `postgres` | PostgreSQL 16 — reports, users, admin accounts |
| `redis` | Redis 7 — bot FSM + rate limiting |
| `backend` | FastAPI API (admin + health) |
| `bot` | Telegram bot (aiogram polling) |
| `admin` | Static admin SPA + nginx reverse proxy |

Public entry point in production: **admin nginx** on `ADMIN_HOST_PORT` (default `80`).
It serves `/admin/` UI and proxies `/admin/*` API + `/healthz` to backend.
PostgreSQL and Redis ports are **not** published.

## 1. Server prerequisites

See `SERVER_REQUIREMENTS.md`.

## 2. Get the project

Prefer a private git clone:

```bash
git clone <PRIVATE_REPO_URL> aerotrust
cd aerotrust
```

Or unpack the company archive (without real `.env`).

## 3. Create `.env`

```bash
cp .env.production.example .env
nano .env   # or vim
```

Replace at least:

- `POSTGRES_PASSWORD` (and the same password inside `DATABASE_URL`)
- `ADMIN_JWT_SECRET` (long random string)
- `TELEGRAM_BOT_TOKEN`

See `SECRETS_REQUIRED.md`.

## 4. Deploy

From the project root:

```bash
bash infra/scripts/deploy_vps.sh
```

Or manually:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm --no-deps backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d backend bot admin
```

## 5. Bootstrap once

Create admin user:

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email admin --password '<STRONG_PASSWORD>' --role admin
```

Create invite code for employees:

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U aerotrust -d aerotrust -c \
  "INSERT INTO invite_codes (code, is_active, max_uses, used_count)
   VALUES ('SAFE-REPORT', true, 100, 0)
   ON CONFLICT DO NOTHING;"
```

Optional resolver (zone-scoped):

```bash
docker compose -f docker-compose.prod.yml exec backend \
  create-admin-user --email resolver@example.com --password '<STRONG_PASSWORD>' \
  --role resolver --zone process
```

## 6. Verify

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${ADMIN_HOST_PORT:-80}/admin/
```

Open admin UI: `http://<server-ip-or-domain>/admin/`  
Login with the admin credentials created above.

Bot smoke:

1. Open the bot in Telegram → `/start`
2. Enter invite code
3. Submit a test report
4. Confirm it appears in admin → Reports

## 7. Logs

```bash
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs -f bot
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f admin
docker compose -f docker-compose.prod.yml ps
```

## 8. Data persistence (critical)

Named volumes (do **not** use `docker compose down -v` in production):

| Volume | Contents |
|--------|----------|
| `aerotrust_postgres_data` | All reports / users / invite codes |
| `aerotrust_uploads_data` | Attachment files |
| `aerotrust_redis_data` | Bot FSM / rate-limit state (non-critical) |

`docker compose down` (without `-v`) keeps volumes.
`docker compose down -v` **deletes** the database and uploads.

## 9. Backup / restore

See commands in `CHECKLIST_BEFORE_PROD.md` and:

```bash
bash infra/scripts/backup_postgres.sh
bash infra/scripts/backup_uploads.sh
```

Restore example:

```bash
# Stop writers first if possible
gunzip -c backups/aerotrust_YYYYMMDD.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aerotrust -d aerotrust
```

## 10. Update / redeploy

```bash
git pull   # or rsync new code
bash infra/scripts/deploy_vps.sh
```

Migrations run as part of deploy. Always backup DB before major updates.

## 11. HTTPS / domain

Compose exposes plain HTTP on `ADMIN_HOST_PORT`.
For production, put TLS in front (host nginx, Caddy, Traefik, or cloud LB) and proxy to the admin container.

`TODO: проверить вручную` — DNS A-запись, сертификат Let's Encrypt, firewall (only 80/443 public).
