#!/usr/bin/env bash
# DEPRECATED — канон: ./loop/loop.sh
# Этот файл остаётся только как thin redirect; удалим в следующем спринте.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "DEPRECATED: ./scripts/loop.sh → используй ./loop/loop.sh" >&2
exec "$ROOT/loop/loop.sh" "$@"
