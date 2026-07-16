#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILES=(-f docker-compose.prod.yml)
ENV_FILE=".env"

compose() {
  docker compose "${COMPOSE_FILES[@]}" "$@"
}

build_images_with_fallback() {
  local build_log
  build_log="$(mktemp)"

  set +e
  compose build 2>&1 | tee "${build_log}"
  local build_status=$?
  set -e

  if [[ ${build_status} -eq 0 ]]; then
    rm -f "${build_log}"
    return 0
  fi

  if ! grep -qiE "toomanyrequests|429[[:space:]]+too[[:space:]]+many[[:space:]]+requests|pull rate limit" "${build_log}"; then
    echo "ERROR: image build failed (not a Docker Hub rate-limit case)."
    rm -f "${build_log}"
    return "${build_status}"
  fi

  echo "WARN: Docker Hub rate limit detected during build."
  echo "==> Retrying build without pulling new base layers"
  set +e
  compose build --pull=false
  local no_pull_status=$?
  set -e

  if [[ ${no_pull_status} -eq 0 ]]; then
    rm -f "${build_log}"
    return 0
  fi

  if ! docker image inspect aerotrust-backend:latest >/dev/null 2>&1; then
    echo "ERROR: no local 'aerotrust-backend:latest' image for fallback rebuild."
    rm -f "${build_log}"
    return "${no_pull_status}"
  fi

  echo "WARN: fallback build for backend from local cached image."
  local hotfix_dockerfile
  hotfix_dockerfile="$(mktemp)"
  cat >"${hotfix_dockerfile}" <<'EOF'
FROM aerotrust-backend:latest
WORKDIR /app
COPY backend /app
EOF
  docker build -f "${hotfix_dockerfile}" -t aerotrust-backend:latest .
  rm -f "${hotfix_dockerfile}" "${build_log}"

  echo "WARN: fallback rebuilt backend image only."
  echo "WARN: bot/admin images were not rebuilt in this fallback path."
}

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
compose config >/dev/null

echo "==> Building images"
build_images_with_fallback

echo "==> Starting dependencies"
compose up -d postgres redis

echo "==> Applying alembic migrations"
compose run --rm --no-deps backend alembic upgrade head

echo "==> Starting backend, bot, admin"
compose up -d backend bot admin

echo "==> Container status"
compose ps

ADMIN_PORT="$(grep -E '^ADMIN_HOST_PORT=' .env | tail -n1 | cut -d= -f2- | tr -d '\r' || true)"
ADMIN_PORT="${ADMIN_PORT:-80}"

if command -v curl >/dev/null 2>&1; then
  echo "==> Health checks"
  curl -fsS "http://127.0.0.1:${ADMIN_PORT}/healthz" >/dev/null
  # Root is now a 301 redirect to /admin/, so follow redirects (-L).
  curl -fsSL "http://127.0.0.1:${ADMIN_PORT}/" >/dev/null
  curl -fsS "http://127.0.0.1:${ADMIN_PORT}/admin/" >/dev/null
  echo "Health checks passed."
else
  echo "curl is not installed, skip HTTP checks."
fi

echo "Deployment completed."
