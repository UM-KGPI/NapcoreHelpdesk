#!/usr/bin/env bash
set -euo pipefail

export PATH="/Applications/Docker.app/Contents/Resources/bin:${PATH}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${ROOT_DIR}/.backups/${STAMP}"
mkdir -p "${OUT_DIR}"

DB_CONTAINER="napcorehelpdesk-db-1"
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
  echo "PostgreSQL container ${DB_CONTAINER} is not running."
  exit 1
fi

for db in napcore_helpdesk digital_twin; do
  if docker exec -i "${DB_CONTAINER}" psql -U napcore -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1; then
    docker exec -i "${DB_CONTAINER}" pg_dump -U napcore -d "${db}" > "${OUT_DIR}/${db}.sql"
  fi
done

if docker ps --format '{{.Names}}' | grep -q '^napcorehelpdesk-graphdb-1$'; then
  docker exec -i napcorehelpdesk-graphdb-1 sh -lc 'tar -czf - -C /opt/graphdb/home . ' > "${OUT_DIR}/graphdb-home.tar.gz"
fi

echo "Backup completed: ${OUT_DIR}"
