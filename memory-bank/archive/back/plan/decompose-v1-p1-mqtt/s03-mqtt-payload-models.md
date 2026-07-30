# Шаг s03: MQTT payload pydantic models
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-COL-05) — **closed** | **tdd:** yes
**AC:** AC-MQTT-10, AC-MQTT-14, AC-MQTT-15 (schema layer)

- **Creative:** [CR-COL-05 / creative-collector-mqtt-contract.md](../../creative/v1-p1-mqtt/creative-collector-mqtt-contract.md) — topic taxonomy hybrid, payload schema v1.0, `@type` + topic validate

**code_surface:** model

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Typed pydantic v2 models для 4 типов сообщений Канонерки: AnalogChannel, DiscreteChannel, LogicalEvent, ExhaustGasGroup + JSON parse/validate entrypoint.

## Контекст
- **Consumes:** CR-COL-05 (topic→type routing, field names, enum codes); plan §4.2
- **Produces:** parser models + `parse_mqtt_payload(topic, json) → typed payload | ParseError`

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/parser.py` (Создание)
- `apps/edge/collector/src/collector/plugins/mqtt/payloads.py` (Создание)
- `apps/edge/collector/tests/fixtures/mqtt/` (Создание — analog/discrete/event/egt JSON)
- `apps/edge/collector/tests/unit/test_mqtt_parser.py` (Создание)

## Интерфейсы (lean — без кода)
- enum: `AnalogApsState`, `DiscreteApsState`, `LogicalEventState` — коды из plan §4.2 (proposal до CR-COL-05)
- model: `AnalogChannelPayload` — value, threshold_vvu/vu/nu/nnu, control_enabled×4, aps_state, channel_test_enabled, channel_id, source_ts
- model: `DiscreteChannelPayload` — aps_state, input_active, channel_test_enabled, channel_id
- model: `LogicalEventPayload` — event_state, input_active, channel_test_enabled, channel_id
- model: `ExhaustGasGroupPayload` — cylinder_deviation[], engine_mean_temp, max_allowed_deviation, operator bounds, cylinder_correction[], aps_permission[]
- fn: `parse_mqtt_payload(topic, data: dict|bytes) → PayloadUnion`
- error: `MqttParseError` — field path + reason; не raises generic JSON errors наружу

## TDD (красная → зелёная)
1. **Тест:** golden fixtures → correct type; invalid enum → MqttParseError; missing required field → error with path
2. **Запуск:** тесты падают.
3. **Реализация:** models per CR-COL-05 + stub fixtures aligned with plan proposal.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. ~~**BLOCKED** до CR-COL-05~~ — **unblocked:** финальные имена полей, `@type` discriminator, `source_ts` — см. [creative-collector-mqtt-contract.md](../../creative/v1-p1-mqtt/creative-collector-mqtt-contract.md) §3.
2. После CREATIVE: экспорт JSON Schema для Канонерки (optional artifact in creative).
3. Topic suffix или payload `@type` определяет union member (CR-COL-05 decision).
4. Fixtures в `tests/fixtures/mqtt/` — канон для s09 integration.

## Чекпоинт верификации
- 4 fixture types parse без ошибок
- unknown channel type → explicit ParseError
- version field in payload (if CR-COL-05) preserved in model
