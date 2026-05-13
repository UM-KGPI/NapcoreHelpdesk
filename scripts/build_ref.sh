#!/usr/bin/env bash
set -euo pipefail

count="$(git rev-list --count HEAD 2>/dev/null || echo 0)"
sha="$(git rev-parse --short=12 HEAD 2>/dev/null || echo nogit)"

echo "build.$count.$sha"
