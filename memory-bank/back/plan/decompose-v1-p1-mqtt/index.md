# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-mqtt
**План:** [plan-v1-p1-mqtt.md](../plan-v1-p1-mqtt.md)
**Implement index:** [implement-v1-p1-mqtt/index.md](../../implement/implement-v1-p1-mqtt/index.md)
**Дата:** 2026-07-27
**Режим:** BACK DECOMPOSE
**Уровень:** L4 (T-008)

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.md`. Интерфейсы — **lean** (без тел/полного кода).

> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность шагов, files/AC/TDD boundaries |
| `architecture-patterns` | plugin adapter B1, reuse T-001 framework |

**Per-step канон** (не дублировать пути здесь): каждый `sNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.

| `code_surface` | Шаги (T-008) |
|----------------|--------------|
| `model` | s01, s03 |
| `service` | s02, s04–s06, s08, s10, s11 (+ anti-patterns) |
| `infra` | s07, s12 |
| `test` | s09 |

## CREATIVE blockers (до IMPLEMENT зависимых шагов)

| ID | Шаги | Артефакт | Статус |
|----|------|----------|--------|
| **CR-COL-05** ✅ | s03, s04, s05, s06, s10 | [creative-collector-mqtt-contract.md](../../creative/creative-collector-mqtt-contract.md) | **closed** 2026-07-27 |
| CR-COL-05b | s08, s09 (fidelity) | split optional из CR-COL-05 | recommended |

**Рекомендуемый порядок CREATIVE:** CR-COL-05 (обязателен) → затем IMPLEMENT s03→s06, s10.

**До CREATIVE можно IMPLEMENT (scaffold):** s01, s02, s07.

**Параллельно с T-001:** T-001 s18–s25 Modbus/OPC emulator **не блокирует** T-008.

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-mqtt-config-models.md](s01-mqtt-config-models.md)<br>• pydantic MqttSourceConfig, I1 publish guard | [s01…](../../implement/implement-v1-p1-mqtt/s01-mqtt-config-models.md) | no | yes | BACK IMPLEMENT | done |
| **s02** | [s02-mqtt-client-wrapper.md](s02-mqtt-client-wrapper.md)<br>• async connect/subscribe/reconnect (aiomqtt) | [s02…](../../implement/implement-v1-p1-mqtt/s02-mqtt-client-wrapper.md) | no | yes | BACK IMPLEMENT | done |
| **s03** | [s03-mqtt-payload-models.md](s03-mqtt-payload-models.md)<br>• Analog/Discrete/Event/EGT pydantic types | [s03…](../../implement/implement-v1-p1-mqtt/s03-mqtt-payload-models.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s04** | [s04-mqtt-lifecycle-tracker.md](s04-mqtt-lifecycle-tracker.md)<br>• state machine + Event emission | [s04…](../../implement/implement-v1-p1-mqtt/s04-mqtt-lifecycle-tracker.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s05** | [s05-mqtt-semantic-mapper.md](s05-mqtt-semantic-mapper.md)<br>• payload → RawSample + Event | [s05…](../../implement/implement-v1-p1-mqtt/s05-mqtt-semantic-mapper.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s06** | [s06-mqtt-connector.md](s06-mqtt-connector.md)<br>• MqttConnector + PluginRegistry register | [s06…](../../implement/implement-v1-p1-mqtt/s06-mqtt-connector.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s07** | [s07-mqtt-channel-maps-stub.md](s07-mqtt-channel-maps-stub.md)<br>• ship-pack mqtt_channels yaml stub | [s07…](../../implement/implement-v1-p1-mqtt/s07-mqtt-channel-maps-stub.md) | no | yes | BACK IMPLEMENT | done |
| **s08** | [s08-emulator-mqtt-publisher.md](s08-emulator-mqtt-publisher.md)<br>• I3 MQTT publisher adapter | [s08…](../../implement/implement-v1-p1-mqtt/s08-emulator-mqtt-publisher.md) | no | yes | BACK IMPLEMENT | done |
| **s09** | [s09-integration-mqtt.md](s09-integration-mqtt.md)<br>• testcontainer E2E mosquitto + collector | [s09…](../../implement/implement-v1-p1-mqtt/s09-integration-mqtt.md) | no | yes | BACK IMPLEMENT | done |
| **s10** | [s10-normalizer-mqtt-bridge.md](s10-normalizer-mqtt-bridge.md)<br>• B4 wire: disable EventDetector for mqtt tags | [s10…](../../implement/implement-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s11** | [s11-health-mqtt.md](s11-health-mqtt.md)<br>• health snapshot fields per mqtt source | [s11…](../../implement/implement-v1-p1-mqtt/s11-health-mqtt.md) | no | yes | BACK IMPLEMENT | done |
| **s12** | [s12-compose-mqtt-dev.md](s12-compose-mqtt-dev.md)<br>• docker-compose profile mqtt-dev + mosquitto | [s12…](../../implement/implement-v1-p1-mqtt/s12-compose-mqtt-dev.md) | no | no | BACK IMPLEMENT | done |

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

## Summary-чеклист

- [x] s01 — MqttSourceConfig + publish guard (I1)
- [x] s02 — async MQTT client wrapper (connect/subscribe/reconnect)
- [ ] s03 — payload pydantic models (Analog/Discrete/Event/EGT)
- [x] s04 — MqttLifecycleTracker + Event on transition
- [x] s05 — MqttSemanticMapper → RawSample + Event
- [x] s06 — MqttConnector + PluginRegistry `mqtt`
- [x] s07 — mqtt_channels yaml stub (APS/GEU)
- [x] s08 — I3 MqttPublisher emulator adapter
- [x] s09 — integration E2E Mosquitto + collector (R-1 Topic fix)
- [x] s10 — Normalizer bridge (mqtt tags, no reconstruction)
- [x] s11 — HealthAggregator mqtt fields
- [x] s12 — compose profile mqtt-dev

## Handoff

- **Done:** BACK DECOMPOSE T-008 — 12 шагов (s01–s12)
- **Files:** `memory-bank/back/plan/decompose-v1-p1-mqtt/`
- **CREATIVE blocker:** CR-COL-05 ✅ closed → s03–s06, s10 unblocked
- **Recommended IMPLEMENT order:** s01 → s02 → s03 → s04 → s05 → s06 → s07 → s09 → s08 → s10 → s11 → s12
- **Scaffold без CREATIVE:** s01, s02, s07 (можно начинать сразу)
- **load_now:** `memory-bank/back/plan/decompose-v1-p1-mqtt/s01-mqtt-config-models.md`
- **Tool / model:** Cursor + fast-editing для s01/s02; Claude Code + premium-coding для s03–s06 semantic stack
- **New chat:** yes — one chat = one atomic subtask
