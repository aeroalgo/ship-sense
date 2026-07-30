# Implement index — T-008 v1 p1 mqtt

**Plan ID:** v1-p1-mqtt  
**Дата:** 2026-07-27  
**Режим:** BACK IMPLEMENT

**Plan:** [plan-v1-p1-mqtt.md](../../plan/plan-v1-p1-mqtt.md)  
**Decompose:** [decompose-v1-p1-mqtt/index.md](../../plan/decompose-v1-p1-mqtt/index.md)

## Реестр шагов (decompose ↔ implement)

> Статусы — только в `implement/sNN-*.md` (источник истины) и `decompose/index.md` (агрегатор). Этот файл — навигационный портал. Без status-колонки.

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** | [s01-mqtt-config-models.md](../../plan/decompose-v1-p1-mqtt/s01-mqtt-config-models.md) | [s01-mqtt-config-models.md](s01-mqtt-config-models.md) |
| **s02** | [s02-mqtt-client-wrapper.md](../../plan/decompose-v1-p1-mqtt/s02-mqtt-client-wrapper.md) | [s02-mqtt-client-wrapper.md](s02-mqtt-client-wrapper.md) |
| **s03** | [s03-mqtt-payload-models.md](../../plan/decompose-v1-p1-mqtt/s03-mqtt-payload-models.md) | [s03-mqtt-payload-models.md](s03-mqtt-payload-models.md) |
| **s04** | [s04-mqtt-lifecycle-tracker.md](../../plan/decompose-v1-p1-mqtt/s04-mqtt-lifecycle-tracker.md) | [s04-mqtt-lifecycle-tracker.md](s04-mqtt-lifecycle-tracker.md) |
| **s05** | [s05-mqtt-semantic-mapper.md](../../plan/decompose-v1-p1-mqtt/s05-mqtt-semantic-mapper.md) | [s05-mqtt-semantic-mapper.md](s05-mqtt-semantic-mapper.md) |
| **s06** | [s06-mqtt-connector.md](../../plan/decompose-v1-p1-mqtt/s06-mqtt-connector.md) | [s06-mqtt-connector.md](s06-mqtt-connector.md) |
| **s07** | [s07-mqtt-channel-maps-stub.md](../../plan/decompose-v1-p1-mqtt/s07-mqtt-channel-maps-stub.md) | [s07-mqtt-channel-maps-stub.md](s07-mqtt-channel-maps-stub.md) |
| **s08** | [s08-emulator-mqtt-publisher.md](../../plan/decompose-v1-p1-mqtt/s08-emulator-mqtt-publisher.md) | [s08-emulator-mqtt-publisher.md](s08-emulator-mqtt-publisher.md) |
| **s09** | [s09-integration-mqtt.md](../../plan/decompose-v1-p1-mqtt/s09-integration-mqtt.md) | [s09-integration-mqtt.md](s09-integration-mqtt.md) |
| **s10** | [s10-normalizer-mqtt-bridge.md](../../plan/decompose-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md) | [s10-normalizer-mqtt-bridge.md](s10-normalizer-mqtt-bridge.md) |
| **s11** | [s11-health-mqtt.md](../../plan/decompose-v1-p1-mqtt/s11-health-mqtt.md) | [s11-health-mqtt.md](s11-health-mqtt.md) |
| **s12** | [s12-compose-mqtt-dev.md](../../plan/decompose-v1-p1-mqtt/s12-compose-mqtt-dev.md) | [s12-compose-mqtt-dev.md](s12-compose-mqtt-dev.md) |

Навигация и Handoff — только `activeContext.md`. Статусы шагов — `decompose/index.md` + `implement/sNN`.
