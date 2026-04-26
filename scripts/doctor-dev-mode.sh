#!/usr/bin/env bash
set -euo pipefail

export PATH="/Applications/Docker.app/Contents/Resources/bin:${PATH}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! docker ps --format '{{.Names}}' | grep -q '^napcorehelpdesk-backend-1$'; then
  echo "Backend container is not running."
  exit 1
fi

echo "=== Dev Doctor ==="
DB_HOST="$(docker exec -i napcorehelpdesk-backend-1 sh -lc 'printf "%s" "$POSTGRES_HOST"')"
DB_NAME="$(docker exec -i napcorehelpdesk-backend-1 sh -lc 'printf "%s" "$POSTGRES_DB"')"
DB_USER="$(docker exec -i napcorehelpdesk-backend-1 sh -lc 'printf "%s" "$POSTGRES_USER"')"

echo "Backend DB target: host=${DB_HOST} db=${DB_NAME} user=${DB_USER}"

if docker ps --format '{{.Names}}' | grep -q '^napcorehelpdesk-db-1$'; then
  echo "Local Compose DB container: running"
else
  echo "Local Compose DB container: not running"
fi

if [[ "${DB_HOST}" == "db" ]]; then
  echo "Mode: local-db"
else
  echo "Mode: external-db"
fi

echo "Backend health:"
for endpoint in live ready; do
  ok=0
  for _ in 1 2 3 4 5; do
    if curl -fsS "http://localhost:8000/api/v1/health/${endpoint}"; then
      echo
      ok=1
      break
    fi
    sleep 1
  done
  if [[ "${ok}" -ne 1 ]]; then
    echo "Health check failed for ${endpoint} after retries."
    exit 1
  fi
done
