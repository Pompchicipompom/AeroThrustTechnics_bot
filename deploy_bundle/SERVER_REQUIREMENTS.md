# Server requirements

## OS

- Ubuntu 22.04 / 24.04 LTS (recommended) or any Linux with Docker Engine
- x86_64 or ARM64

## Software

- Docker Engine 24+
- Docker Compose plugin v2 (`docker compose version`)
- Optional: `curl`, `git`, `openssl`

Install helper (Ubuntu):

```bash
bash infra/scripts/install_docker_ubuntu.sh
```

## Hardware (MVP)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB SSD | 40+ GB SSD |
| Network | outbound HTTPS to Telegram API | same |

Disk grows with attachments under the `uploads_data` volume.

## Ports

| Port | Purpose | Public? |
|------|---------|---------|
| `ADMIN_HOST_PORT` (default 80) | Admin UI + API proxy + `/healthz` | Yes (or via TLS proxy) |
| 443 | HTTPS (if TLS terminator on host) | Yes |
| 5432 Postgres | DB | **No** — not published by compose |
| 6379 Redis | Cache/FSM | **No** — not published |
| 8000 Backend | Internal only in prod | **No** in prod compose |

## Outbound access

Bot uses **long polling** to Telegram:

- `https://api.telegram.org` must be reachable from the server
- No inbound webhook port required for the bot

If Telegram IPv6 is flaky on the VPS, keep `BOT_FORCE_IPV4=true` (default).

## Domain / TLS

- Domain or public IP for admin UI
- TLS certificate recommended (Let's Encrypt)
- `TODO: проверить вручную` — company firewall / WAF rules

## Accounts needed from the company

1. Telegram Bot Token (BotFather)
2. SSH access (if vendor deploys) with Docker permissions
3. Domain DNS control (if HTTPS on company domain)
4. Strong passwords / JWT secret (or ask vendor to generate and hand over via secure channel)
