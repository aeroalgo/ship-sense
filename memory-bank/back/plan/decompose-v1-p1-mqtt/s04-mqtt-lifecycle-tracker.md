# Шаг s04: MqttLifecycleTracker — state machine + Event emission
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-COL-05) — **closed** | **tdd:** yes
**AC:** AC-MQTT-12, AC-MQTT-13, AC-MQTT-21

- **Creative:** [CR-COL-05 / creative-collector-mqtt-contract.md](../../creative/creative-collector-mqtt-contract.md) — lifecycle mapping tables, silent seed, idempotency_key, native passthrough

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
In-memory tracker prev/next lifecycle per `(source_id, channel_id)`; emit ровно один `Event` на transition; idempotency_key по plan §5.2.

## Контекст
- **Consumes:** s03 payload enums; T-001 s01 `Event` domain model; CR-COL-05 lifecycle mapping tables
- **Produces:** `MqttLifecycleTracker` — замена EventDetector для mqtt-native path

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/lifecycle_tracker.py` (Создание)
- `apps/edge/collector/tests/unit/test_mqtt_lifecycle_tracker.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `MqttLifecycleTracker` — state dict keyed by (source_id, channel_id)
- method: `observe(channel_id, aps_state, source_ts, kind) → Event | None`
- mapping: Kanoner enum → canonical `params.lifecycle` (Q4-A: normal/exceeded_unacked/returned_unacked/exceeded_acked/blocked/…)
- event fields: event_name (`aps.threshold.exceeded`, …), params.lifecycle, params.reconstructed=false, idempotency_key
- dedup: same (source_id, channel_id, lifecycle, source_ts) → no second Event

## TDD (красная → зелёная)
1. **Тест:** transition sequences — only one event per change; no event on repeat state; returned_unacked and blocked distinct in params
2. **Запуск:** тесты падают.
3. **Реализация:** pure state machine + mapping table from CR-COL-05.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Mapping tables per channel kind (analog threshold vs discrete vs logical event) — из CR-COL-05.
2. First observation: optional initial Event or silent seed (CREATIVE decision).
3. `params.reconstructed` always false for mqtt path (AC-MQTT-13).
4. Thread-safe/async-safe: one tracker instance per source connector.

## Чекпоинт верификации
- duplicate same state → None
- lifecycle transition → exactly one Event with correct idempotency_key
- `returned_unacked`, `blocked` не схлопываются в generic cleared/active
