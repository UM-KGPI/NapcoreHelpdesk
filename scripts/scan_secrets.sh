#!/usr/bin/env bash
set -euo pipefail

patterns=(
  'github_pat_[A-Za-z0-9_]{20,}'
  'ghp_[A-Za-z0-9]{20,}'
  'gho_[A-Za-z0-9]{20,}'
  'ghu_[A-Za-z0-9]{20,}'
  'ghs_[A-Za-z0-9]{20,}'
  'sk-[A-Za-z0-9]{20,}'
  'AIza[0-9A-Za-z_-]{35}'
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
)

regex=$(IFS='|'; printf '%s' "${patterns[*]}")
tmp_file=$(mktemp)

if git grep -n -I -E "$regex" -- . ':(exclude).venv' ':(exclude)frontend/node_modules' ':(exclude)backend/db.sqlite3' >"$tmp_file" 2>/dev/null; then
  echo "Potential secrets detected:" >&2
  cat "$tmp_file" >&2
  rm -f "$tmp_file"
  exit 1
fi

rm -f "$tmp_file"
echo "Secret scan passed."
