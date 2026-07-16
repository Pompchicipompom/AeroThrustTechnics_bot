# Audit report — AeroThrust Trusted Messages MVP

Date: 2026-07-16  
Scope: local repository + Docker stack readiness for transfer to a company server.

## What was checked

1. Project structure (bot, backend, admin, postgres, redis, nginx-in-admin)
2. Telegram bot: token from env, handlers, attachments, errors, rate limit
3. Backend/API: health, auth, RBAC, error handlers, OpenAPI in prod
4. Admin UI: API base URL, empty states, roles at API layer
5. Database: PostgreSQL + Alembic + Docker volumes
6. Docker Compose (dev + prod)
7. Uploads persistence and path safety
8. Secrets / `.env*` / `.gitignore`
9. Security: exposed ports, JWT, anonymity in API/UI
10. Logs / deploy scripts / documentation package `deploy_bundle/`
11. Local smoke: running stack health, persistence after restart

## Architecture (as-is)

```
Telegram ←polling→ bot ──┬──► PostgreSQL (reports, users, admin_users, …)
                         ├──► Redis (FSM + rate limit)
                         └──► uploads volume
Browser → admin(nginx|vite) → backend(FastAPI) → PostgreSQL + uploads
```

## Findings

### Critical / high (fixed in this audit)

| Issue | Fix |
|-------|-----|
| `PyJWT` used in code but missing from `pyproject.toml` | Added explicit dependency |
| Dev `.env.example` incomplete vs `Settings` | Fully aligned with config |
| Dev Redis without volume (FSM lost on recreate) | Added `redis_data` volume to `docker-compose.yml` |
| Dev backend without healthcheck; admin didn't wait healthy | Healthcheck + `service_healthy` |
| Prod OpenAPI/docs exposed | Disabled when `APP_ENV=prod\|production` |
| No max length on report text | `MAX_REPORT_TEXT_LENGTH` (default 4000) in bot |
| Brittle hardcoded Telegram IP in prod compose | Removed; rely on `BOT_FORCE_IPV4` |
| Missing production docs / secrets handoff | Added `deploy_bundle/` + backup scripts |
| `.gitignore` gaps (`.DS_Store`, `.env.production`, dumps) | Expanded |

### Medium (documented, not rewritten)

| Issue | Status |
|-------|--------|
| Anonymous reports still store `author_user_id` in DB (hidden in admin API/UI) | By design for “my reports” in bot; DB-level deanonymization possible with raw SQL access — document for company |
| `require_roles()` helper unused at route layer; zone RBAC enforced in repositories | Works for admin/resolver scopes; route-level decorator optional improvement |
| No CORS middleware | OK for same-origin nginx/vite proxy; needed only if SPA hosted on another origin |
| `infra/nginx/default.conf` not used by compose | Orphan helper; left in place (not deleted) |
| `docs/04_env_example.env` outdated vs real settings | Listed as stale planning doc; real source is `.env*.example` |
| Integration tests use `create_all` not Alembic | Drift risk; CI should still run Alembic on deploy |
| Prod fallback in `deploy_vps.sh` may rebuild only backend image on Hub rate limit | Documented operational risk |

### Low / leftovers (not deleted)

| Item | Note |
|------|------|
| `README_FOR_CODEX.md` | Internal agent notes — keep |
| `infra/docker/README.md` | Placeholder |
| Multiple nginx backup filenames historically on old VPS | N/A in this clean repo |
| Local `.env` with real token | Gitignored; rotate if ever leaked |

### Garbage candidates (not deleted — none present as build artifacts)

- No `node_modules`, `__pycache__`, `.DS_Store`, `*.bak` in clean clone
- Do not delete `docs/*` or `infra/nginx/default.conf` without company confirmation

## Security notes

- Admin API requires JWT except `POST /admin/auth/login`
- Postgres/Redis not published in prod compose
- Admin UI hides author for `submit_mode=anonymous`
- Open (non-anonymous) mode still shows technical id + telegram username — product feature
- `TODO: проверить вручную` — TLS terminator, password policy, token rotation, host firewall

## Data loss incident context (ops)

On the previous shared VPS, AeroThrust Postgres volume was already gone before this audit.
This package hardens against recurrence: named volumes, backup scripts, explicit “never `down -v`” docs.

## Smoke test results (this machine)

| Check | Result |
|-------|--------|
| `GET /healthz` | OK |
| Admin UI HTTP | 200 on `:5173` |
| Admin login + reports list | OK (JWT + probe report visible) |
| Bot polling | Running (`@AeroThrustTechnics_bot`) |
| Data after `docker compose restart` | OK — probe report still in Postgres |
| Redis named volume | Created (`aerotrust_redis_data`) |
| Unit tests (`test_rate_limit`, `test_report_flow_attachments`) | 8 passed |
| `docker-compose.prod.yml config` | OK |
| Prod admin image build (`Dockerfile.prod`) | OK |
| Secret scan of tracked files vs local `.env` token | none |
| Full Telegram e2e new report via bot UI | `TODO: проверить вручную` |
| Integration pytest suite (needs test DB) | `TODO: проверить вручную` |
| HTTPS / company domain | `TODO: проверить вручную` |

## Files added / changed

### Added

- `deploy_bundle/*` (8 docs)
- `infra/scripts/backup_postgres.sh`
- `infra/scripts/backup_uploads.sh`

### Updated

- `backend/pyproject.toml` — PyJWT
- `backend/app/core/config.py` — max text length
- `backend/app/bot/handlers/report_flow.py` — enforce max text
- `backend/app/main.py` — hide docs in prod
- `.env.example`, `.env.production.example`
- `.gitignore`
- `docker-compose.yml` — redis volume + healthchecks
- `docker-compose.prod.yml` — remove hardcoded Telegram IP
- `README.md` — ops/logs/backup pointers

## How to run (short)

**Dev:**

```bash
cp .env.example .env   # fill TELEGRAM_BOT_TOKEN
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

**Prod:**

```bash
cp .env.production.example .env   # fill secrets
bash infra/scripts/deploy_vps.sh
```

## Remaining risks for the company

1. No automated nightly backups until cron is configured
2. Anonymity is API/UI-level, not cryptographic unlinkability in DB
3. Single-host Docker MVP — no HA/replicas
4. Telegram polling depends on outbound network reliability
5. Admin port is HTTP unless they add TLS

## What to clarify with the company

- Domain + HTTPS ownership
- Who stores Telegram token / admin passwords
- Backup retention policy
- Whether open (non-anonymous) submit mode should remain enabled
- SSH access if vendor deploys
