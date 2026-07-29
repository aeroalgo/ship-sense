#!/bin/bash
set -euo pipefail

echo "Starting TimescaleDB container..."
docker compose --profile storage-dev up -d db

echo "Waiting for database to be ready..."
TIMEOUT=30
ELAPSED=0
until docker compose --profile storage-dev exec -T db pg_isready -U shipsense >/dev/null 2>&1; do
    if [ "${ELAPSED}" -ge "${TIMEOUT}" ]; then
        echo "Timeout waiting for database to start"
        exit 1
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

echo "Database is ready!"
