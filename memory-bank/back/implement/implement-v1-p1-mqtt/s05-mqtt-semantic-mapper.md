# T-008 | s05 | mqtt-semantic-mapper IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s05-mqtt-semantic-mapper.md](../../plan/decompose-v1-p1-mqtt/s05-mqtt-semantic-mapper.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Создан `MqttSemanticMapper` и публичный `MapResult(samples, event, quarantine_reason)`, чтобы отделить transport/parser от semantic mapping.
- Analog payload преобразуется в primary `RawSample` со scalar `raw_value`; при `thresholds.expose=true` добавляются четыре pseudo-samples с native IDs `{channel_id}#VVU|VU|NU|NNU` по ADR-COL-05-03.
- Discrete и logical event payloads преобразуются в boolean `RawSample`; lifecycle state передаётся в `MqttLifecycleTracker`.
- Lifecycle transition возвращается через `MapResult.event`, включая native event params из tracker (`reconstructed=false`, test mode и idempotency).
- ExhaustGasGroup расширяется в 12 per-cylinder deviation `RawSample` с native IDs `{channel_id}#CYL{n}.DEV`; corrections и permissions остаются отдельным downstream mapping scope, не выдумываются mapper-ом без channel-map contract.
- Unknown `channel_id` не отбрасывается: создаётся quarantine-marked sample с `native_quality=mqtt.quarantine.unknown_channel` и `quarantine_reason=unknown_channel`.
- Mapper принимает как mapping-like channel map, так и объект с `lookup(channel_id)`, поэтому совместим с будущим s07 `MqttChannelMap`.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/mapper.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/tests/unit/test_mqtt_mapper.py`

## TDD

- RED: targeted запуск нового теста завершился `ModuleNotFoundError: No module named 'collector.plugins.mqtt.mapper'`.
- GREEN: после реализации mapper и исправления expectation quarantine targeted тесты прошли.

## Тесты

- `cd apps/edge/collector && PYTHONPATH=src:../emulator/src pytest -q tests/unit/test_mqtt_mapper.py` → **5 passed**.
- `cd apps/edge/collector && PYTHONPATH=src:../emulator/src pytest -q tests/unit/test_mqtt_mapper.py tests/unit/test_mqtt_lifecycle_tracker.py tests/unit/test_mqtt_parser.py` → **23 passed**.
- `cd apps/edge/collector && python -m compileall -q src/collector/plugins/mqtt tests/unit/test_mqtt_mapper.py` → **passed**.
- Проверка длины строк `awk 'length($0)>79 {print FNR ":" length($0)}'` для mapper/test → **пусто**.

## Integration check

- [x] parser payload → mapper → `RawSample` scalar path
- [x] threshold pseudo-samples используют channel-native IDs, предусмотренные CR-COL-05
- [x] lifecycle event passthrough не реконструируется mapper-ом
- [x] EGT deviation expansion даёт 12 cylinder samples
- [x] unknown channel не является silent drop и несёт quarantine reason
- [ ] s07 channel map loader должен зарегистрировать pseudo-tag entries с unit/tag_id для downstream Normalizer
- [ ] s06 connector должен передать один и тот же `source_id` lifecycle tracker и mapper
