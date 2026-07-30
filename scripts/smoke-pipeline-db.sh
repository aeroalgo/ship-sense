#!/usr/bin/env bash
set -Eeuo pipefail

# L2 compose smoke: poll SQL COUNT(samples) > 0.
#
# Usage:
#   scripts/smoke-pipeline-db.sh [default|mqtt]
#   TIMEOUT=120 scripts/smoke-pipeline-db.sh mqtt
#
# default: compose up db writer emulator collector (no profile)
# mqtt:    compose --profile mqtt-dev up db writer mosquitto collector-mqtt emulator-mqtt
#
# Exit:
#   0 — samples count > 0 within TIMEOUT
#   1 — count still 0 after timeout (FAIL loud)
#   2 — usage / unsupported mode

MODE="${1:-default}"
TIMEOUT="${TIMEOUT:-60}"
POLL_INTERVAL=2

if [[ "$MODE" != "default" && "$MODE" != "mqtt" ]]; then
  echo "Usage: $0 [default|mqtt]" >&2
  echo "  default — docker compose (no profile): db writer emulator collector" >&2
  echo "  mqtt    — docker compose --profile mqtt-dev: db writer mosquitto collector-mqtt emulator-mqtt" >&2
  exit 2
fi

COMPOSE=(docker compose)
if [[ "$MODE" == "mqtt" ]]; then
  COMPOSE=(docker compose --profile mqtt-dev)
fi

log() {
  echo "[$(date '+%H:%M:%S')] $*" >&2
}

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

cleanup() {
  local status=$?
  if [[ $status -ne 0 ]]; then
    log "Smoke failed; dumping recent writer logs"
    "${COMPOSE[@]}" logs --no-color --tail=50 writer 2>&1 || true
  fi
  # Do NOT down compose — this is a smoke probe, not a teardown harness.
  exit "$status"
}
trap cleanup EXIT

log "MODE=$MODE TIMEOUT=${TIMEOUT}s"

# Bring up required services (idempotent if already running).
if [[ "$MODE" == "default" ]]; then
  log "Starting default profile services (db, writer, emulator, collector)..."
  "${COMPOSE[@]}" up -d --build db writer emulator collector
else
  log "Starting mqtt-dev profile services (db, writer, mosquitto, collector-mqtt, emulator-mqtt)..."
  "${COMPOSE[@]}" up -d --build db writer mosquitto collector-mqtt emulator-mqtt
fi

# Wait for db to be healthy (psql reachable).
deadline=$(( $(date +%s) + 60 ))
log "Waiting for db health (pg_isready)..."
while [[ $(date +%s) -lt $deadline ]]; do
  if "${COMPOSE[@]}" exec -T db pg_isready -U shipsense -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
    log "db healthy"
    break
  fi
  sleep 1
done

if ! "${COMPOSE[@]}" exec -T db pg_isready -U shipsense -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  fail "db did not become healthy within 60s"
fi

# Poll COUNT(*) FROM samples until >0 or timeout.
deadline=$(( $(date +%s) + TIMEOUT ))
log "Polling samples count (interval=${POLL_INTERVAL}s, timeout=${TIMEOUT}s)..."
count=0
while [[ $(date +%s) -lt $deadline ]]; do
  count=$("${COMPOSE[@]}" exec -T db \
    psql -U shipsense -d shipsense -Atc 'SELECT count(*) FROM samples' 2>/dev/null || echo "0")
  # Trim whitespace/newlines.
  count=$(echo "$count" | tr -d ' \t\r\n')
  if [[ "$count" =~ ^[0-9]+$ ]] && [[ "$count" -gt 0 ]]; then
    log "samples count=$count"
    if [[ "$MODE" == "mqtt" ]]; then
      # AC-PIPE-08: expect TAI4101 or TGEU4101 present.
      has_tag=$("${COMPOSE[@]}" exec -T db \
        psql -U shipsense -d shipsense -Atc \
        "SELECT count(*) FROM samples WHERE tag_id IN ('TAI4101','TGEU4101')" 2>/dev/null || echo "0")
      has_tag=$(echo "$has_tag" | tr -d ' \t\r\n')
      if [[ "$has_tag" =~ ^[0-9]+$ ]] && [[ "$has_tag" -gt 0 ]]; then
        log "AC-PIPE-08: found tag TAI4101 or TGEU4101 (count=$has_tag)"
      else
        log "WARNING: AC-PIPE-08 — no TAI4101/TGEU4101 yet (count=$has_tag), but samples>0"
      fi
    fi
    echo "PASS: samples count=$count (>0) within ${TIMEOUT}s (MODE=$MODE)"
    exit 0
  fi
  sleep "$POLL_INTERVAL"
done

# Timeout path — fail loud.
fail "samples still 0 after ${TIMEOUT}s (MODE=$MODE)"
