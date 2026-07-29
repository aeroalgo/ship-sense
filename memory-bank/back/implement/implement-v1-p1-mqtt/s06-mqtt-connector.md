# T-008 | s06 | mqtt-connector IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s06-mqtt-connector.md](../../plan/decompose-v1-p1-mqtt/s06-mqtt-connector.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлен `MqttConnector` поверх `BaseSourceConnector`: subscribe-only transport, parser и semantic mapper соединены в один callback pipeline.
- Реализован raw sample callback, optional event callback и last-value cache для `read()`.
- Добавлены локальные метрики `messages_received`, `parse_errors`, `last_msg_ts`; ошибки парсинга логируются и не останавливают коннектор.
- `PluginRegistry` регистрирует MQTT factory в runtime bootstrap; factory загружает channel map и создаёт отдельный connector для каждого source config.
- Повторная подписка на тот же MQTT topic filter не дублируется в client wrapper.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/connector.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/src/collector/plugins/mqtt/client.py`
- `apps/edge/collector/src/collector/runtime/bootstrap.py`
- `apps/edge/collector/tests/unit/test_mqtt_connector.py`

## TDD

- RED: targeted запуск нового теста завершился `ModuleNotFoundError: No module named 'collector.plugins.mqtt.connector'`.
- GREEN: после реализации connector, client dedupe и runtime registration targeted MQTT/registry тесты прошли.

## Тесты

- `PYTHONPATH=apps/edge/collector/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_mqtt_connector.py apps/edge/collector/tests/unit/test_mqtt_client.py apps/edge/collector/tests/unit/test_mqtt_parser.py apps/edge/collector/tests/unit/test_mqtt_mapper.py apps/edge/collector/tests/unit/test_plugin_registry.py` → **36 passed**.
- `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m compileall -q apps/edge/collector/src/collector/plugins/mqtt apps/edge/collector/src/collector/runtime/bootstrap.py apps/edge/collector/tests/unit/test_mqtt_connector.py` → **passed**.
- Проверка длины строк в connector/test файлах → пусто; в bootstrap остались исторические строки >79 символов, новые MQTT-строки без превышения.

## Integration check

- [x] `PluginRegistry.create(config)` возвращает `MqttConnector` после runtime registration.
- [x] MQTT topic filter берётся из `MqttSourceConfig.subscribe` и подписывается в subscribe push path.
- [x] bytes → `parse_mqtt_payload` → `MqttSemanticMapper` → `RawSample` callback.
- [x] malformed JSON увеличивает `parse_errors`, логируется, connector остаётся жив.
- [x] два connector instance имеют независимые metrics/cache/lifecycle tracker.
- [x] publish path не добавлен; client wrapper остаётся subscribe-only.
- [ ] s07 channel map loader должен добавить реальные MQTT maps APS/GEU.
- [ ] s11 health snapshot должен расширить публичный snapshot mqtt-полями.
