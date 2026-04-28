#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILES=(-f docker-compose.prod.yml)
ENV_FILE=".env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found."
  echo "Create it from .env.production.example and fill secrets first."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed."
  echo "Run infra/scripts/install_docker_ubuntu.sh (Ubuntu) or install Docker manually."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose plugin is not installed."
  echo "Install docker-compose-plugin package."
  exit 1
fi

echo "==> Validating compose config"
docker compose "${COMPOSE_FILES[@]}" config >/dev/null

echo "==> Building images"
docker compose "${COMPOSE_FILES[@]}" build

echo "==> Starting dependencies"
docker compose "${COMPOSE_FILES[@]}" up -d postgres redis

echo "==> Applying alembic migrations"
docker compose "${COMPOSE_FILES[@]}" run --rm migrate

echo "==> Starting backend, bot, admin"
docker compose "${COMPOSE_FILES[@]}" up -d backend bot admin

echo "==> Container status"
docker compose "${COMPOSE_FILES[@]}" ps

ADMIN_PORT="$(grep -E '^ADMIN_HOST_PORT=' .env | tail -n1 | cut -d= -f2- | tr -d '\r' || true)"
ADMIN_PORT="${ADMIN_PORT:-80}"

if command -v curl >/dev/null 2>&1; then
  echo "==> Health checks"
  curl -fsS "http://127.0.0.1:${ADMIN_PORT}/healthz" >/dev/null
  curl -fsS "http://127.0.0.1:${ADMIN_PORT}/" >/dev/null
  echo "Health checks passed."
else
  echo "curl is not installed, skip HTTP checks."
fi

echo "Deployment completed."
