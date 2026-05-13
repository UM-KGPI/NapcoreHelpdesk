#!/usr/bin/env bash
set -euo pipefail

part="${1:-patch}"
version_file="VERSION"

if [[ ! -f "$version_file" ]]; then
  echo "ERROR: VERSION file not found at repository root" >&2
  exit 1
fi

current="$(tr -d '[:space:]' < "$version_file")"
if [[ ! "$current" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "ERROR: VERSION must be SemVer core format x.y.z (found: $current)" >&2
  exit 1
fi

major="${BASH_REMATCH[1]}"
minor="${BASH_REMATCH[2]}"
patch="${BASH_REMATCH[3]}"

case "$part" in
  patch)
    patch=$((patch + 1))
    ;;
  minor)
    minor=$((minor + 1))
    patch=0
    ;;
  major)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
  *)
    echo "Usage: $0 [patch|minor|major]" >&2
    exit 1
    ;;
esac

next="$major.$minor.$patch"
printf '%s\n' "$next" > "$version_file"

echo "VERSION: $current -> $next"
