#!/usr/bin/env bash
set -Eeuo pipefail

MODE="${1:-single}"
COMPOSE=(docker compose --profile mqtt-dev)
EMULATOR_CONTAINER=""
PANELS="aps"

if [[ "$MODE" == "dual" || "$MODE" == "events" ]]; then
  PANELS="aps,geu"
fi

cleanup() {
  local status=$?
  if [[ -n "$EMULATOR_CONTAINER" ]]; then
    docker rm -f "$EMULATOR_CONTAINER" >/dev/null 2>&1 || true
  fi
  if [[ "$status" -ne 0 ]]; then
    echo "Smoke failed; dumping compose logs" >&2
    "${COMPOSE[@]}" logs --no-color writer collector-mqtt emulator-mqtt 2>&1 || true
  fi
  "${COMPOSE[@]}" down --remove-orphans >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT

if [[ "$MODE" != "single" && "$MODE" != "dual" && "$MODE" != "events" && "$MODE" != "sigterm" ]]; then
  echo "Unsupported mode: $MODE (use single, dual, events, or sigterm)" >&2
  exit 2
fi

"${COMPOSE[@]}" build emulator-mqtt
"${COMPOSE[@]}" up -d --build mosquitto writer collector-mqtt

EMULATOR_CONTAINER=$("${COMPOSE[@]}" run --rm -d --no-deps emulator-mqtt \
  --broker mqtt://mosquitto:1883 \
  --panels "$PANELS" \
  --interval 1.0)

if [[ "$MODE" == "dual" ]]; then
  sleep 15
  for ((attempt = 1; attempt <= 30; attempt++)); do
    if "${COMPOSE[@]}" exec -T collector-mqtt python -c '
import json
from pathlib import Path

snapshot = json.loads(Path("/var/lib/shipsense/health/collector.json").read_text())
sources = {entry["source_id"]: entry for entry in snapshot.get("sources", [])}
required = ("panel_aps", "panel_geu")
if not all(source_id in sources for source_id in required):
    raise SystemExit("missing required MQTT sources")
for source_id in required:
    entry = sources[source_id]
    if entry.get("subscribed") is not True:
        raise SystemExit(f"{source_id} is not subscribed")
    if entry.get("last_msg_ts") is None:
        raise SystemExit(f"{source_id} has no message timestamp")
print("health snapshot contains two live MQTT sources")
' >/dev/null 2>&1; then
      echo "PASS: dual-panel MQTT smoke (aps, geu)"
      exit 0
    fi
    sleep 1
  done

  echo "FAIL: health snapshot did not contain two live MQTT sources within 30s" >&2
  exit 1
fi

if [[ "$MODE" == "events" ]]; then
  sleep 15
  for ((attempt = 1; attempt <= 60; attempt++)); do
    if "${COMPOSE[@]}" logs --no-color writer 2>&1 | grep -Eq 'total_events=[1-9][0-9]*'; then
      echo "PASS: lifecycle event smoke (aps, geu) — total_events > 0"
      exit 0
    fi
    sleep 1
  done
  echo "FAIL: writer did not report total_events > 0 within 60s" >&2
  exit 1
fi

if [[ "$MODE" == "sigterm" ]]; then
  # Wait for collector to be subscribed before stopping (AC-HLT-05 regression)
  sleep 10
  for ((attempt = 1; attempt <= 30; attempt++)); do
    if "${COMPOSE[@]}" exec -T collector-mqtt python -c '
import json
from pathlib import Path

snapshot = json.loads(Path("/var/lib/shipsense/health/collector.json").read_text())
sources = {entry["source_id"]: entry for entry in snapshot.get("sources", [])}
entry = sources.get("panel_aps")
if entry is None or entry.get("subscribed") is not True:
    raise SystemExit("panel_aps not subscribed yet")
print("panel_aps subscribed")
' >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # docker compose stop = SIGTERM → stop_grace_period → SIGKILL
  "${COMPOSE[@]}" stop collector-mqtt

  exit_code=$(docker inspect -f '{{.State.ExitCode}}' shipsense-collector-mqtt 2>/dev/null || echo "missing")

  if [[ "$exit_code" != "0" ]]; then
    echo "FAIL: collector-mqtt ExitCode=$exit_code (expected 0 — drain did not fit grace)" >&2
    docker inspect -f '{{json .State}}' shipsense-collector-mqtt >&2 || true
    exit 1
  fi

  echo "PASS: SIGTERM drain — collector-mqtt ExitCode 0 (AC-HLT-05)"
  exit 0
fi

for ((attempt = 1; attempt <= 30; attempt++)); do
  if "${COMPOSE[@]}" logs --no-color writer 2>&1 | grep -Eq 'total_samples=[1-9][0-9]*'; then
    echo "PASS: single-panel MQTT smoke (aps)"
    exit 0
  fi
  sleep 1
done

echo "FAIL: writer did not receive samples within 30s" >&2
exit 1
