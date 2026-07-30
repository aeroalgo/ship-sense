# [T-008 | s10 | normalizer-mqtt-bridge] IMPLEMENT
**Plan ID:** v1-p1-mqtt
**Decompose step:** [s10-normalizer-mqtt-bridge.md](../../plan/decompose-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-28
**Уровень:** L2
**Статус:** done

## Сделано
- Добавлен `Normalizer.process_event(event)` для passthrough MQTT-native `Event` без реконструкции.
- Добавлен dedup native events по `Event.idempotency_key`.
- `EventDetector` не вызывается для `TagMapEntry` с `source: mqtt` или `skip_event_detector: true`; scalar telemetry path не изменён.
- Добавлены unit-тесты для MQTT skip-detector, Modbus detector и native event dedup/passthrough.

## Файлы
- `apps/edge/collector/src/collector/core/normalizer.py`
- `apps/edge/collector/tests/unit/test_normalizer_mqtt.py`

## Тесты
- red: новые тесты падали на отсутствии MQTT skip-detector и `Normalizer.process_event`.
- cmd: `PYTHONPATH=apps/edge/collector/src:apps/edge/collector/tests:apps/edge/emulator/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_normalizer.py apps/edge/collector/tests/unit/test_normalizer_mqtt.py -q`
- итог: **10 passed**, 1 предупреждение от `testcontainers`.

## Integration check
- [x] MQTT-native `Event.params.reconstructed` сохраняется без изменений.
- [x] Duplicate native events с одинаковым `idempotency_key` отбрасываются.
- [x] MQTT telemetry остаётся scalar raw path.
- [x] Modbus/discrete path продолжает использовать `EventDetector`.

