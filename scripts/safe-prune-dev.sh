#!/usr/bin/env bash
set -euo pipefail

export PATH="/Applications/Docker.app/Contents/Resources/bin:${PATH}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "=== Safe Prune (Dev) ==="
echo "Step 1/4: Doctor check"
bash scripts/doctor-dev-mode.sh

echo "Step 2/4: Backup"
bash scripts/backup-dev-data.sh

echo "Step 3/4: Baseline disk usage"
docker system df

echo "Step 4/4: Prune unused images and builder cache"
docker image prune -f
docker builder prune -f

if [[ "${PRUNE_VOLUMES:-0}" == "1" ]]; then
  echo "Optional volume prune enabled (PRUNE_VOLUMES=1)."
  docker volume prune -f
fi

echo "=== Post-prune disk usage ==="
docker system df
