# Checklist before production

## Code / package

- [ ] Private repo access OR clean project archive without `.env` / `node_modules` / caches
- [ ] `deploy_bundle/` included
- [ ] `.env.production.example` reviewed
- [ ] No real tokens in git history for the handoff branch

## Server

- [ ] Docker + Compose installed
- [ ] Disk space OK (attachments grow)
- [ ] Outbound access to `api.telegram.org`
- [ ] Firewall: only needed ports open (80/443)
- [ ] Postgres/Redis not exposed publicly

## Secrets

- [ ] Strong `POSTGRES_PASSWORD`
- [ ] Matching password in `DATABASE_URL`
- [ ] Strong unique `ADMIN_JWT_SECRET` (not `change-me-for-prod`)
- [ ] Valid `TELEGRAM_BOT_TOKEN`
- [ ] Strong admin password (not README examples)
- [ ] `APP_ENV=prod`

## First boot

- [ ] `bash infra/scripts/deploy_vps.sh` succeeds
- [ ] `curl /healthz` returns `status: ok`
- [ ] `/admin/` loads
- [ ] Admin user created
- [ ] Invite code created
- [ ] Bot `/start` + invite works
- [ ] Test report appears in admin
- [ ] Status change works
- [ ] Attachment upload (if used) works and is downloadable in admin

## Persistence

- [ ] Team knows: **never** `docker compose down -v` on prod
- [ ] Backup script tested once
- [ ] Volumes listed and documented for the hoster

### Backup commands (PostgreSQL)

```bash
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aerotrust aerotrust | gzip > "backups/aerotrust_$(date +%Y%m%d_%H%M%S).sql.gz"
```

Or: `bash infra/scripts/backup_postgres.sh`

### Backup uploads

```bash
bash infra/scripts/backup_uploads.sh
```

### Restore DB (destructive — replaces data)

```bash
gunzip -c backups/aerotrust_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aerotrust -d aerotrust
```

### Restart safety check

```bash
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml ps
# confirm reports still present in admin UI
```

## Security

- [ ] TLS in front of admin (recommended)
- [ ] Default README passwords not used
- [ ] `/docs` unavailable when `APP_ENV=prod`
- [ ] Admin login required for reports API
- [ ] Anonymous reports hide author in admin UI/API

## Manual TODOs

- [ ] `TODO: проверить вручную` — HTTPS certificate + domain
- [ ] `TODO: проверить вручную` — company SSO / VPN if required
- [ ] `TODO: проверить вручную` — Telegram bot privacy settings / description
- [ ] `TODO: проверить вручную` — nightly backup cron on host
- [ ] `TODO: проверить вручную` — monitoring / uptime alerts
