#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_TEMPLATE="${ROOT_DIR}/scripts/graphdb-repo-config.template.ttl"
GRAPHDB_ENDPOINT="${GRAPHDB_SPARQL_ENDPOINT:-http://localhost:7200}"
GRAPHDB_BASE_URL="${GRAPHDB_ENDPOINT%/repositories/*}"
GRAPHDB_REPOSITORY_ID="${GRAPHDB_REPOSITORY:-napcore-helpdesk}"
GRAPHDB_REPOSITORY_TITLE="${GRAPHDB_REPOSITORY_TITLE:-NAPCORE Helpdesk GraphDB}"
GRAPHDB_STARTUP_TIMEOUT_SECONDS="${GRAPHDB_STARTUP_TIMEOUT_SECONDS:-120}"

if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to initialize the GraphDB repository." >&2
    exit 1
fi

if [[ ! -f "${CONFIG_TEMPLATE}" ]]; then
    echo "Missing GraphDB repository config template: ${CONFIG_TEMPLATE}" >&2
    exit 1
fi

curl_args=(-fsS)
if [[ -n "${GRAPHDB_USER:-}" ]]; then
    curl_args+=(-u "${GRAPHDB_USER}:${GRAPHDB_PASSWORD:-}")
fi

deadline=$((SECONDS + GRAPHDB_STARTUP_TIMEOUT_SECONDS))
until curl "${curl_args[@]}" "${GRAPHDB_BASE_URL}/rest/repositories" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
        echo "Timed out waiting for GraphDB at ${GRAPHDB_BASE_URL}." >&2
        exit 1
    fi
    sleep 2
done

repositories_json="$(curl "${curl_args[@]}" "${GRAPHDB_BASE_URL}/rest/repositories")"
if printf '%s' "${repositories_json}" | grep -Eq '"id"[[:space:]]*:[[:space:]]*"'"${GRAPHDB_REPOSITORY_ID}"'"'; then
    echo "GraphDB repository ${GRAPHDB_REPOSITORY_ID} already exists."
    exit 0
fi

tmp_config="$(mktemp)"
trap 'rm -f "${tmp_config}"' EXIT

sed \
    -e "s|__REPOSITORY_ID__|${GRAPHDB_REPOSITORY_ID}|g" \
    -e "s|__REPOSITORY_TITLE__|${GRAPHDB_REPOSITORY_TITLE}|g" \
    "${CONFIG_TEMPLATE}" > "${tmp_config}"

curl "${curl_args[@]}" -X POST \
    "${GRAPHDB_BASE_URL}/rest/repositories" \
    -H "Content-Type: multipart/form-data" \
    -F "config=@${tmp_config}"

echo "Created GraphDB repository ${GRAPHDB_REPOSITORY_ID}."
