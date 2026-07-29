# T-008 | s03 | mqtt-payload-models IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s03-mqtt-payload-models.md](../../plan/decompose-v1-p1-mqtt/s03-mqtt-payload-models.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлены строгие Pydantic v2 payload-модели для `analog`, `discrete`, `event` и `egt`.
- Добавлены wire enums `AnalogApsState`, `DiscreteApsState`, `LogicalEventState`.
- Добавлен обязательный `schema_version` с поддержкой major `1`, timezone-aware UTC `source_ts` и `@type` alias.
- Добавлен `parse_mqtt_payload(topic, data)` для dict/bytes: topic-first routing, проверка версии/kind/channel/type и typed `MqttParseError`.
- EGT-контракт валидирует 12 значений для deviation/correction/permission.
- Добавлены golden fixtures для четырёх типов сообщений.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/payloads.py`
- `apps/edge/collector/src/collector/plugins/mqtt/parser.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/tests/fixtures/mqtt/analog.json`
- `apps/edge/collector/tests/fixtures/mqtt/discrete.json`
- `apps/edge/collector/tests/fixtures/mqtt/event.json`
- `apps/edge/collector/tests/fixtures/mqtt/egt.json`
- `apps/edge/collector/tests/unit/test_mqtt_parser.py`

## TDD

- RED: `ModuleNotFoundError: No module named 'collector.plugins.mqtt.parser'`.
- GREEN: parser/models/fixtures добавлены; targeted тесты проходят.

## Тесты

- `PYTHONPATH=apps/edge/collector/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_mqtt_parser.py apps/edge/collector/tests/unit/test_mqtt_config.py apps/edge/collector/tests/unit/test_mqtt_client.py` → **18 passed**.
- `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m compileall -q apps/edge/collector/src/collector/plugins/mqtt apps/edge/collector/tests/unit/test_mqtt_parser.py` → **passed**.

## Integration check

- [x] topic kind `analog|discrete|event|egt` маршрутизирует в typed model
- [x] `@type` зеркалирует topic kind и mismatch даёт `type_topic_mismatch`
- [x] channel id из topic сверяется с payload
- [x] invalid enum/missing field дают `MqttParseError` с field path
- [x] malformed bytes JSON дают `invalid_json`, не generic JSON error
- [x] schema major и timestamp contract валидируются на schema layer
- [ ] connector/semantic mapper — следующий s04–s06
