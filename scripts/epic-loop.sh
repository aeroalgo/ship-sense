#!/usr/bin/env bash
# DEPRECATED — канон: ./loop/loop.sh --track epic
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "DEPRECATED: ./scripts/epic-loop.sh → используй ./loop/loop.sh --track epic" >&2
exec "$ROOT/loop/loop.sh" --track epic "$@"
