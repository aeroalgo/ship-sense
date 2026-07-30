# Шаг s02: compose-сервис `emulator-mqtt` + ACL publish
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S02, AC-MQTT-S07
**code_surface:** infra
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Добавить compose-сервис `emulator-mqtt` в профиль `mqtt-dev`, который запускает `python -m emulator.mqtt_publish` против `mosquitto:1883` с панелями `aps,geu`. Разрешить анониму **publish** в `aclfile` (сейчас только `read`). Провалидировать весь overlay `docker compose --profile mqtt-dev config` exit 0.

## Контекст
- **Consumes:** s01 `emulator.mqtt_publish` entrypoint; s12 родителя (compose `mosquitto`/`collector-mqtt`, `aclfile`, `mosquitto.conf`).
- **Produces:** compose-сервис; правка aclfile; валидируемый overlay.

## Файлы
- `docker-compose.yml` (Модификация — добавить сервис `emulator-mqtt`)
- `infra/mosquitto/aclfile` (Модификация — разрешить publish анониму)
- `infra/mosquitto/mosquitto.conf` (Verify — без изменений, если уже корректен)

## Текущее состояние (verified 2026-07-29)
- `mosquitto.conf`: `listener 1883 0.0.0.0`, `allow_anonymous true`, `acl_file ...` — корректен (verify-only).
- `aclfile`: только `topic read shipsense/#` → publish deny по умолчанию в Mosquitto 2 ACL mode. **Требует** `topic write shipsense/#` (или `topic readwrite shipsense/#`) для анонимного publisher.
- compose: сервис `collector-mqtt` уже depends_on `mosquitto` + `writer`.

## Интерфейсы (lean — без кода)
- Сервис `emulator-mqtt`:
  - `build: context: apps/edge/emulator` (тот же image path, что и для modbus/opc emulator).
  - `container_name: shipsense-emulator-mqtt`
  - `profiles: ["mqtt-dev"]`
  - `command: ["python", "-m", "emulator.mqtt_publish", "--broker", "mqtt://mosquitto:1883", "--panels", "aps,geu", "--interval", "1.0"]`
  - `depends_on: { mosquitto: { condition: service_started } }` (broker не обязан быть healthy, publisher сам reconect; mosquitto без healthcheck сейчас).
  - `restart: unless-stopped` (publisher может стартовать раньше broker — restart покрывает; s05/lifecycle — parent).
  - `stop_grace_period: 10s` (SIGTERM drain, AC-MQTT-S05).
- `aclfile`: заменить `topic read shipsense/#` → `topic readwrite shipsense/#` (dev-only; documented как known limit в s07).

## TDD (нет)
- **Причина:** compose/infra wiring без бизнес-логики; `MqttPublisherAdapter` и `mqtt_publish` уже покрыты (s01).
- **Верификация (parent):**
  1. `docker compose --profile mqtt-dev config` → exit 0 (AC-MQTT-S07).
  2. `docker compose --profile mqtt-dev up -d mosquitto` → publisher сможет подключиться (manual, s03 полный smoke).

## Подробный процесс выполнения
1. Добавить сервис `emulator-mqtt` в `docker-compose.yml` рядом с `collector-mqtt` (после `mosquitto`).
2. Правка `aclfile`: `topic readwrite shipsense/#` (dev-only). Комментарий в файле: «dev only — production uses authenticated publisher ACL».
3. Verify `mosquitto.conf` без правок (listener 1883 + allow_anonymous true уже есть).
4. `docker compose --profile mqtt-dev config` — exit 0.

## Anti-patterns checklist
- Не дублировать build context / image — reuse `apps/edge/emulator`.
- `stop_grace_period` указан явно (graceful drain, не hard kill).
- restart policy не маскирует баг — только для broker-race при старте.

## Чекпоинт верификации
- AC-MQTT-S02: `docker compose --profile mqtt-dev up -d emulator-mqtt` → `docker compose --profile mqtt-dev ps` = `emulator-mqtt` running.
- AC-MQTT-S07: `docker compose --profile mqtt-dev config` → exit 0.

## Зависимости
- Upstream: s01 (entrypoint) — hard.
- Parallel: s01 (нет общей файловой поверхности) — можно параллельно.

## Frontend
N/A.

## Следующий шаг
→ s03 (single-panel smoke: aps → writer samples/sec > 0).
