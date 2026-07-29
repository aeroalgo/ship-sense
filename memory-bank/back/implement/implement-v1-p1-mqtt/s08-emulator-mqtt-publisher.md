# T-008 | s08 | emulator MQTT publisher IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s08-emulator-mqtt-publisher.md](../../plan/decompose-v1-p1-mqtt/s08-emulator-mqtt-publisher.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлен publish-only `MqttPublisherAdapter` в emulator process без импортов Modbus/OPC или collector MQTT transport.
- Реализованы panel profiles `aps` и `geu` с topic taxonomy `shipsense/v1/{panel}/{kind}/{channel_id}`.
- `build_messages(tick)` формирует четыре контрактных payload kind: `analog`, `discrete`, `event`, `egt` с `@type`, `schema_version: "1.0"`, `channel_id` и UTC `source_ts`.
- Lifecycle states переходят детерминированно по tick; analog/discrete/event используют соответствующие proposal enums.
- Значения и EGT vectors воспроизводятся при одинаковом seed и tick sequence.
- Реализован async `connect(broker_url)`, publish-only `publish_loop(iterations=...)` и идемпотентный `stop()` через aiomqtt-compatible context factory.
- Добавлена runtime dependency `aiomqtt==2.4.0` и экспорт адаптера из `emulator.protocols`.

## Файлы

- `apps/edge/emulator/src/emulator/protocols/mqtt_publisher.py`
- `apps/edge/emulator/src/emulator/protocols/__init__.py`
- `apps/edge/emulator/tests/test_mqtt_publisher.py`
- `apps/edge/emulator/requirements.txt`

## TDD

- RED: targeted запуск нового теста завершился `ModuleNotFoundError: No module named 'emulator.protocols.mqtt_publisher'`.
- GREEN: после реализации adapter targeted tests прошли.

## Тесты

- `PYTHONPATH=apps/edge/emulator/src .venv/bin/pytest -q --confcutdir=apps/edge/emulator/tests apps/edge/emulator/tests/test_mqtt_publisher.py` → **3 passed**.
- `PYTHONPATH=apps/edge/emulator/src:apps/edge/collector/src .venv/bin/python - <<'PY' ... parse_mqtt_payload ... PY` → **4 payloads parsed**.
- `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m compileall -q apps/edge/emulator/src/emulator/protocols/mqtt_publisher.py apps/edge/emulator/tests/test_mqtt_publisher.py` → **passed**.

## Integration check

- [x] `MqttPublisherAdapter` publishes all four payload kinds.
- [x] Fixed seed produces identical message sequence for identical ticks.
- [x] Topics and JSON payloads conform to CR-COL-05 hybrid taxonomy and schema v1.0.
- [x] MQTT publisher module has no Modbus/OPC imports and does not reuse register mappings.
- [x] Async connect/publish/stop lifecycle is isolated behind aiomqtt-compatible client factory.
- [ ] Collector-to-broker E2E remains s09 scope.
- [ ] Final KKS/channel table remains proposal stub pending Kanonerka.
