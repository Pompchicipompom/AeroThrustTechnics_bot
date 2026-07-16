#!/usr/bin/env bash
# Backup PostgreSQL volume data via pg_dump (safe while containers run).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="${BACKUP_DIR}/aerotrust_${STAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "ERROR: ${COMPOSE_FILE} not found in ${ROOT_DIR}"
  exit 1
fi

echo "==> Dumping database to ${OUT}"
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-aerotrust}" "${POSTGRES_DB:-aerotrust}" \
  | gzip > "${OUT}"

echo "OK: ${OUT}"
ls -lh "${OUT}"
