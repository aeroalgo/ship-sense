#!/usr/bin/env bash
# DEPRECATED — канон: ./loop/loop.sh --track program
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "DEPRECATED: ./scripts/program-loop.sh → используй ./loop/loop.sh --track program" >&2
exec "$ROOT/loop/loop.sh" --track program "$@"
