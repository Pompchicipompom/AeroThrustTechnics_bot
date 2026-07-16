# Secrets required (do not put these in git)

Pass these to the company's IT via a secure channel (password manager, sealed note, 1:1 handoff).
**Never** put real values into the repository, deploy archive, Slack/email plain text if avoidable, or screenshots.

## Required

| Secret / value | Env var | Where used |
|----------------|---------|------------|
| Telegram Bot Token | `TELEGRAM_BOT_TOKEN` | bot container |
| PostgreSQL password | `POSTGRES_PASSWORD` | postgres + `DATABASE_URL` |
| Database URL | `DATABASE_URL` | backend + bot (`postgresql+asyncpg://USER:PASSWORD@postgres:5432/DB`) |
| Admin JWT signing secret | `ADMIN_JWT_SECRET` | backend admin auth |
| Admin UI login email | (bootstrap CLI) | `create-admin-user --email ...` |
| Admin UI login password | (bootstrap CLI) | `create-admin-user --password ...` |

`DATABASE_URL` password **must** match `POSTGRES_PASSWORD`.

## Strongly recommended

| Item | Env var / note |
|------|----------------|
| JWT algorithm | `ADMIN_JWT_ALGORITHM=HS256` (default OK) |
| Access token TTL | `ADMIN_ACCESS_TOKEN_TTL_MINUTES` |
| Public admin port | `ADMIN_HOST_PORT` |
| Invite code(s) | created in DB (`invite_codes`), not env |
| Resolver account(s) | optional `create-admin-user --role resolver --zone ...` |
| Domain / public URL | for TLS reverse proxy (not required by app env today) |

## Optional / already have defaults

| Item | Env var |
|------|---------|
| Force IPv4 for Telegram | `BOT_FORCE_IPV4=true` |
| Rate limits | `BOT_RATE_LIMIT_*` |
| Upload limits | `MAX_ATTACHMENT_*`, `MAX_REPORT_TEXT_LENGTH` |
| Allowed file types | `ALLOWED_DOCUMENT_*` |

## Not used by current code (ignore if seen in old docs)

- `TELEGRAM_WEBHOOK_*` — bot uses polling, not webhooks
- `SECRET_KEY` — not used; use `ADMIN_JWT_SECRET`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` env bootstrap — use CLI `create-admin-user`

## Checklist before handoff

- [ ] Real `.env` is **not** inside the zip/repo
- [ ] Placeholders only in `.env.production.example`
- [ ] Secrets list delivered separately
- [ ] Old Telegram token rotated if it ever leaked into chat/logs/history
