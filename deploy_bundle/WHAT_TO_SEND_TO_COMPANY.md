# What to send to the company

## Preferred

1. **Access to a private Git repository** with this project (branch `main` or a release tag).
2. Folder **`deploy_bundle/`** (already in the repo) as the ops entry point.
3. Secrets from **`SECRETS_REQUIRED.md`** via a **separate secure channel** (not in the repo).

## If git access is not possible

Send a project archive that includes:

- `backend/`, `admin/`, `infra/`, `docs/`, `deploy_bundle/`
- `docker-compose.yml`, `docker-compose.prod.yml`
- `.env.example`, `.env.production.example`
- `README.md`

Exclude:

- `.env` (real secrets)
- `admin/node_modules/`, `admin/dist/`
- Python venv / `__pycache__` / `.pytest_cache`
- DB dumps, uploads, local Docker volumes
- `.git` only if the company does not need history (optional)

## How they run it

- Install Docker + Docker Compose on the company server
- Follow `deploy_bundle/README_DEPLOY.md`
- Fill `.env` from `.env.production.example` using secrets received separately

## If the company wants us to deploy

They should provide:

1. SSH access to the server
2. A user with permission to run Docker (`docker` / root)
3. Domain/DNS (optional but recommended for HTTPS)
4. Telegram bot token and approval to use it on that server

## Do not send

- Real `.env` files inside a shared zip
- Screenshots that contain tokens
- Old server backups that include unrelated projects’ secrets

## Start here (company IT)

1. `deploy_bundle/SERVER_REQUIREMENTS.md`
2. `deploy_bundle/SECRETS_REQUIRED.md` (request secrets)
3. `deploy_bundle/README_DEPLOY.md`
4. `deploy_bundle/CHECKLIST_BEFORE_PROD.md`
5. `deploy_bundle/AUDIT_REPORT.md` (known risks)
