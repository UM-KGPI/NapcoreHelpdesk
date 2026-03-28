#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: bash scripts/validate-openapi.sh <openapi-file>" >&2
  exit 1
fi

spec_file="$1"

if [[ ! -f "$spec_file" ]]; then
  echo "Error: OpenAPI file not found: $spec_file" >&2
  exit 1
fi

# Try available validators in preferred order.
if command -v openapi-generator-cli >/dev/null 2>&1; then
  echo "Validating with openapi-generator-cli"
  openapi-generator-cli validate -i "$spec_file"
  echo "OpenAPI validation passed."
  exit 0
fi

if command -v swagger-cli >/dev/null 2>&1; then
  echo "Validating with swagger-cli"
  swagger-cli validate "$spec_file"
  echo "OpenAPI validation passed."
  exit 0
fi

if command -v redocly >/dev/null 2>&1; then
  echo "Validating with redocly"
  redocly lint "$spec_file"
  echo "OpenAPI validation passed."
  exit 0
fi

echo "Error: no OpenAPI validator found on PATH." >&2
echo "Install one of: openapi-generator-cli, swagger-cli, redocly." >&2
exit 1
