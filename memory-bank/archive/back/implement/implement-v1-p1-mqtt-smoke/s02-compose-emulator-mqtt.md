# [v1-p1-mqtt-smoke | s02 | compose-emulator-mqtt] IMPLEMENT

**Plan ID:** v1-p1-mqtt-smoke
**Decompose step:** [s02-compose-emulator-mqtt.md](../../plan/decompose-v1-p1-mqtt-smoke/s02-compose-emulator-mqtt.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-29
**Уровень:** L1 (infra compose + aclfile; no TDD)
**Статус:** done

> **Skills A∪B:** tdd (N/A), python-testing-patterns (N/A), modern-python (N/A), python-anti-patterns — Read до правок.

## Сделано

- Правка `infra/mosquitto/aclfile`: `topic read shipsense/#` → `topic readwrite shipsense/#` (dev-only, с комментарием: «dev only — production uses authenticated publisher ACL»).
- Добавлен сервис `emulator-mqtt` в `docker-compose.yml` (после `collector-mqtt`, перед `volumes:`):
  - `build: { context: apps/edge/emulator }` — reuse того же image, что и emulator-modbus/opc.
  - `container_name: shipsense-emulator-mqtt`
  - `profiles: ["mqtt-dev"]`
  - `command: ["python", "-m", "emulator.mqtt_publish", "--broker", "mqtt://mosquitto:1883", "--panels", "aps,geu", "--interval", "1.0"]`
  - `depends_on: { mosquitto: { condition: service_started } }` (не healthy — publisher сам reconect).
  - `restart: unless-stopped`
  - `stop_grace_period: 10s` (SIGTERM drain, AC-MQTT-S05).
- Verify `infra/mosquitto/mosquitto.conf` — без изменений (listener 1883 + allow_anonymous true + acl_file уже корректны).
- `docker compose --profile mqtt-dev config` → exit 0 (AC-MQTT-S07).

## Файлы

- `infra/mosquitto/aclfile` (modify, +1 строка, -1 строка)
- `docker-compose.yml` (modify, +18 строк)

## Тесты

- N/A (infra/compose wiring; логика publisher покрыта s01).
- Верификация (parent):
  - `docker compose --profile mqtt-dev config` → exit 0.
  - `docker compose --profile mqtt-dev up -d mosquitto` → publisher сможет подключиться (manual, s03 smoke).

## Integration check

- [x] reuse `apps/edge/emulator` build context — без дублирования Dockerfile/requirements.
- [x] `stop_grace_period` указан явно (graceful drain, не hard kill).
- [x] restart policy не маскирует баг — только для broker-race при старте.
- [x] aclfile: dev-only; production ACL будет через аутентифицированных publisher'ов.
- N/A storage keys / env vars / DB cols / events (infra, no persistence).

## AC-MQTT-S02

`docker compose --profile mqtt-dev up -d emulator-mqtt` → `docker compose --profile mqtt-dev ps` = `emulator-mqtt` running.

## AC-MQTT-S07

`docker compose --profile mqtt-dev config` → exit 0.
