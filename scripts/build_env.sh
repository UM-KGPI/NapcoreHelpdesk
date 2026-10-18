#!/usr/bin/env bash
# Identity of this checkout, as environment variables for docker compose.
#
# Source it from the repository root before running `docker compose` by hand:
#   . scripts/build_env.sh
# scripts/deploy.sh does that for you.
#
#   VITE_APP_VERSION   frontend build argument (version plus build reference)
#   SERVICE_VERSION    backend and Celery: contents of VERSION
#   SERVICE_BUILD_REF  backend and Celery: build.<commit count>.<short sha>
#
# docker-compose.prod.yml passes SERVICE_VERSION and SERVICE_BUILD_REF to the containers as
# environment variables. A changed value makes compose recreate them, so a deployment that
# only changes VERSION cannot leave a container reporting the old version (a single-file
# mount of VERSION keeps showing the old file until the container is recreated).
VITE_APP_VERSION="$(bash scripts/app_version.sh)"
SERVICE_VERSION="$(tr -d '[:space:]' < VERSION)"
SERVICE_BUILD_REF="$(bash scripts/build_ref.sh)"
export VITE_APP_VERSION SERVICE_VERSION SERVICE_BUILD_REF
