#!/usr/bin/env bash
# Wrapper → ./loop/loop.sh --track epic
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/loop/loop.sh" --track epic "$@"
