#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/render-plantuml.sh <path-to-puml> [more-puml-files...]" >&2
  exit 1
fi

if ! command -v plantuml >/dev/null 2>&1; then
  echo "Error: plantuml command not found." >&2
  echo "Install PlantUML and ensure it is available on PATH." >&2
  exit 1
fi

for puml in "$@"; do
  if [[ ! -f "$puml" ]]; then
    echo "Error: file not found: $puml" >&2
    exit 1
  fi

  echo "Rendering $puml -> SVG"
  plantuml -tsvg "$puml"
done

echo "Done."
