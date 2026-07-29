# BACK BUGFIX — MQTT smoke: emulator-mqtt ENTRYPOINT

**Дата:** 2026-07-29  
**Источник:** [qa-20260729-v1-p1-mqtt-smoke.md](../qa/qa-20260729-v1-p1-mqtt-smoke.md)  
**Статус:** done

## Симптом

`scripts/smoke-mqtt-stack.sh single|dual|events` → writer без samples / dual health probe fail. QA атрибутировал circular import (R-1).

## Reproduce

```bash
docker compose --profile mqtt-dev up -d mosquitto emulator-mqtt
docker compose --profile mqtt-dev logs emulator-mqtt
# → unrecognized arguments: python -m emulator.mqtt_publish …
# STATUS Restarting (2)
```

Collector при этом стартует (`sources=2`, MQTT subscribed); `messages_received=0`.

## Root cause

1. Image `shipsense/emulator:dev` имеет `ENTRYPOINT ["python", "-m", "emulator"]` (Modbus/OPC `__main__`). Compose `command:` только заменяет CMD → argv `python -m emulator python -m emulator.mqtt_publish …` → exit 2 → нет publish → нет samples.
2. Dual probe: `compose run collector-mqtt python -c …` глотается `ENTRYPOINT ["python", "-m", "collector"]` → health check всегда fail, даже при живом потоке.

**R-1 (circular import):** на текущем дереве **не воспроизводится** (`import collector.plugins.mqtt.connector` OK; collector boot OK). Writer `127.0.0.1` connect/disconnect = healthcheck stub, не collector.

## Fix

- `docker-compose.yml` `emulator-mqtt`: `entrypoint: ["python", "-m", "emulator.mqtt_publish"]`, `command` = только CLI args.
- `scripts/smoke-mqtt-stack.sh`: `run` emulator с args only; dual health → `exec -T collector-mqtt`.

## Файлы

- `docker-compose.yml`
- `scripts/smoke-mqtt-stack.sh`
- `apps/edge/emulator/tests/test_mqtt_compose_service.py`

## TDD

- red→green: `test_emulator_mqtt_entrypoint_invokes_mqtt_publish_not_modbus_main`
- green: `test_smoke_dual_probes_health_via_exec_not_run`
- `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_mqtt_compose_service.py` → **2 passed**

## Verify

| Mode | Result |
|------|--------|
| single | PASS |
| dual | PASS |
| events | PASS |

## Handoff

- **Done:** ENTRYPOINT override + smoke dual exec probe.
- **Next:** `BACK QA` — повторный QA v1-p1-mqtt-smoke (single/dual/events + suite с pymodbus).
- **New chat:** yes.
