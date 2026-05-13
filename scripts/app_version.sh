#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f VERSION ]]; then
  echo "0.0.0+build.0.nogit"
  exit 0
fi

base="$(tr -d '[:space:]' < VERSION)"
ref="$(bash scripts/build_ref.sh)"

echo "$base+$ref"
