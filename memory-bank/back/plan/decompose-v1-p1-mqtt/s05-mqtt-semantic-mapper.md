# Шаг s05: MqttSemanticMapper — payload → RawSample + Event
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-COL-05) — **closed** | **tdd:** yes
**AC:** AC-MQTT-10, AC-MQTT-11, AC-MQTT-12, AC-MQTT-14, AC-MQTT-15

- **Creative:** [CR-COL-05 / creative-collector-mqtt-contract.md](../../creative/creative-collector-mqtt-contract.md) — pseudo-tags `{tag_id}.{VVU|VU|NU|NNU}`, EGT per-cylinder expansion, quarantine unknown channel

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Mapper: typed payload + channel map → list `RawSample` (value + optional threshold pseudo-tags) + optional `Event` from lifecycle tracker.

## Контекст
- **Consumes:** s03 parser, s04 lifecycle tracker, s07 channel map loader; T-001 `RawSample`
- **Produces:** `MqttSemanticMapper.map(payload, map_entry) → MapResult(samples, event?)`

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/mapper.py` (Создание)
- `apps/edge/collector/tests/unit/test_mqtt_mapper.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `MqttSemanticMapper` — deps: lifecycle_tracker, channel_map
- method: `map(source_id, payload, recv_ts) → MapResult`
- type: `MapResult` — samples: list[RawSample], event: Event | None
- analog: primary RawSample scalar value; thresholds → separate tag_ids per CR-COL-05 (e.g. TAI4101.VVU) OR documented metadata path
- discrete/event: state fields → Event via tracker; optional telemetry for input_active
- egt: N RawSamples per cylinder deviation + aggregate tags per plan §4.2.4
- unknown channel_id → quarantine sample + reason (FR-B-MQTT-11)

## TDD (красная → зелёная)
1. **Тест:** analog fixture → value sample + 4 threshold samples (if CR-COL-05 separate tags); lifecycle change → Event; EGT → 12 cylinder samples
2. **Запуск:** тесты падают.
3. **Реализация:** mapper keeps normalizer dumb — scalar raw_value where possible.
4. **Запуск:** tесты проходят.

## Подробный процесс выполнения
1. ~~**BLOCKED** threshold strategy until CR-COL-05~~ — **unblocked:** pseudo-tags ADR-COL-05-03 в [creative](../../creative/creative-collector-mqtt-contract.md).
2. native_id = channel_id from payload; tag_id from yaml map.
3. source_ts from payload if present else recv_ts.
4. Integrate lifecycle_tracker for aps_state transitions on all kinds.

## Чекпоинт верификации
- analog → correct tag_id, unit, value
- thresholds exposed per creative decision (AC-MQTT-11)
- unknown channel → quarantine, not silent drop
- ExhaustGasGroup → per-cylinder sample count matches fixture
