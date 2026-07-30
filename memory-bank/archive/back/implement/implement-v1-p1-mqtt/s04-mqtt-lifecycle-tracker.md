# T-008 | s04 | mqtt-lifecycle-tracker IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s04-mqtt-lifecycle-tracker.md](../../plan/decompose-v1-p1-mqtt/s04-mqtt-lifecycle-tracker.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Создан `MqttLifecycleTracker` с in-memory state по `(source_id, channel_id)`.
- Реализован silent seed: первая observation сохраняет lifecycle и не эмитит synthetic Event.
- Повторное состояние не эмитит Event; transition эмитит ровно один Event.
- Добавлены нормативные mapping tables для analog, discrete и logical event.
- Сохранены `params.lifecycle`, `params.kanoner_state` и `params.reconstructed=False`.
- Добавлен idempotency key `{source_id}:{channel_id}:{lifecycle}:{source_ts.isoformat()}`.
- `channel_test_enabled=True` не подавляет Event, добавляет `params.test_mode=True` и выставляет `Quality.UNCERTAIN`.
- Enum input проверяется на соответствие lifecycle kind, чтобы не принимать enum другого канала.
- Экспортирован `MqttLifecycleTracker` из MQTT plugin package.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/lifecycle_tracker.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/tests/unit/test_mqtt_lifecycle_tracker.py`

## TDD

- RED: targeted test сначала падал с `ModuleNotFoundError: No module named 'collector.plugins.mqtt.lifecycle_tracker'`.
- GREEN: после реализации и исправления test-mode/type validation targeted tests проходят.

## Тесты

- `PYTHONPATH=src:../emulator/src pytest -q tests/unit/test_mqtt_lifecycle_tracker.py` → **7 passed**.
- `python -m compileall -q src/collector/plugins/mqtt tests/unit/test_mqtt_lifecycle_tracker.py` → **passed**.
- Проверка `awk 'length($0)>79 {print FNR ":" length($0)}' ...` → **пусто**.

## Integration check

- [x] state keyed by `(source_id, channel_id)`
- [x] lifecycle mapping соответствует CR-COL-05 §2
- [x] `returned_unacked` и `blocked` не схлопываются в generic state
- [x] `params.reconstructed=False` для MQTT-native Event
- [x] idempotency key соответствует CR-COL-05 / AC-MQTT-12
- [x] `channel_test_enabled` сохраняет Event и маркирует test mode
- [ ] semantic mapper потребляет tracker — следующий s05
- [ ] connector/runtime отключает reconstruction EventDetector — следующий s06/s10
