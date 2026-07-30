# Implement index — v1 p1 mqtt-smoke
**Plan ID:** v1-p1-mqtt-smoke
**Дата:** 2026-07-29
**Режим:** BACK IMPLEMENT

**Plan:** [plan-v1-p1-mqtt-smoke.md](../../plan/plan-v1-p1-mqtt-smoke.md)
**Decompose:** [decompose-v1-p1-mqtt-smoke/index.md](../../plan/decompose-v1-p1-mqtt-smoke/index.md)

Каждый шаг = один заход IMPLEMENT. Имена файлов совпадают с decompose: `sNN-<slug>.md`.

> **Policy:** статусы живут в `implement/sNN-*.md` (источник истины) и `decompose/index.md` (агрегатор). Этот файл — навигационный hub, без status-колонки.

## Реестр шагов (decompose ↔ implement)

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** | [s01-mqtt-publish-entrypoint.md](../../plan/decompose-v1-p1-mqtt-smoke/s01-mqtt-publish-entrypoint.md) | [s01-mqtt-publish-entrypoint.md](s01-mqtt-publish-entrypoint.md) |
| **s02** | [s02-compose-emulator-mqtt.md](../../plan/decompose-v1-p1-mqtt-smoke/s02-compose-emulator-mqtt.md) | [s02-compose-emulator-mqtt.md](s02-compose-emulator-mqtt.md) |
| **s03** | [s03-smoke-single-panel.md](../../plan/decompose-v1-p1-mqtt-smoke/s03-smoke-single-panel.md) | [s03-smoke-single-panel.md](s03-smoke-single-panel.md) |
| **s04** | [s04-smoke-dual-panel-health.md](../../plan/decompose-v1-p1-mqtt-smoke/s04-smoke-dual-panel-health.md) | [s04-smoke-dual-panel-health.md](s04-smoke-dual-panel-health.md) |
| **s05** | [s05-smoke-lifecycle-events.md](../../plan/decompose-v1-p1-mqtt-smoke/s05-smoke-lifecycle-events.md) | [s05-smoke-lifecycle-events.md](s05-smoke-lifecycle-events.md) |
| **s06** | [s06-smoke-sigterm-drain.md](../../plan/decompose-v1-p1-mqtt-smoke/s06-smoke-sigterm-drain.md) | [s06-smoke-sigterm-drain.md](s06-smoke-sigterm-drain.md) |
| **s07** | [s07-readme-mqtt-smoke.md](../../plan/decompose-v1-p1-mqtt-smoke/s07-readme-mqtt-smoke.md) | [s07-readme-mqtt-smoke.md](s07-readme-mqtt-smoke.md) |
