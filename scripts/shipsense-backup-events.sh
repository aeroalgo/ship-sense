#!/usr/bin/env bash
set -Eeuo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-/mnt/backup}"
SHIP_PACK_DIR="${SHIP_PACK_DIR:-/app/ship-pack}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

exec "${PYTHON_BIN}" -m apps.edge.storage.backup.runner
