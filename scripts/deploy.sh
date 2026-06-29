#!/usr/bin/env bash
# Production deploy script — runs on the server via SSH from GitHub Actions.
# Expected location on server: /opt/napcore-helpdesk/scripts/deploy.sh
set -euo pipefail

REPO_DIR="/opt/napcore-helpdesk"
COMPOSE="docker compose -f ${REPO_DIR}/docker-compose.prod.yml"

cd "${REPO_DIR}"

echo "==> Pulling latest code"
git pull origin main

echo "==> Building images"
${COMPOSE} build --pull

echo "==> Starting services"
${COMPOSE} up -d --remove-orphans

echo "==> Waiting for backend to become healthy"
timeout 90 bash -c "until ${COMPOSE} exec -T backend curl -sf http://localhost:8000/api/v1/health/live; do sleep 3; done"

echo "==> Running migrations"
${COMPOSE} exec -T backend python manage.py migrate --noinput

echo "==> Removing dangling images"
docker image prune -f

echo "==> Deploy complete"
${COMPOSE} ps
