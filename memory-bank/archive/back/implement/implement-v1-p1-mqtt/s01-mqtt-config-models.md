# T-008 | s01 | mqtt-config-models IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s01-mqtt-config-models.md](../../plan/decompose-v1-p1-mqtt/s01-mqtt-config-models.md)  
**Дата:** 2026-07-27  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлены `MqttConnectionConfig`, `MqttSubscribeConfig`, `MqttSourceOptions` и `MqttSourceConfig`.
- MQTT-источники выбираются по `protocol: mqtt` при загрузке `CollectorSettings`.
- Для MQTT-моделей включён `extra="forbid"`; неизвестные поля отклоняются Pydantic.
- `publish_allowed` имеет безопасный default `false`.
- В `validate_config()` добавлен профильный guard: `publish_allowed=true` отклоняется при `profile="prod"` или `COLLECTOR_PROFILE=prod`.
- Карта MQTT берётся из поля `map` и валидируется тем же loader/уникальностью native id.

## Файлы

- `apps/edge/collector/src/collector/config/models.py`
- `apps/edge/collector/src/collector/config/validator.py`
- `apps/edge/collector/src/collector/plugins/mqtt/config.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/tests/unit/test_mqtt_config.py`
- `apps/edge/collector/tests/fixtures/config/mqtt_sources.yaml`
- `apps/edge/collector/tests/fixtures/config/mqtt_sources_unknown_field.yaml`
- `apps/edge/collector/tests/fixtures/config/maps/mqtt_panel_aps.yaml`
- `apps/edge/collector/tests/fixtures/config/maps/mqtt_panel_geu.yaml`

## Тесты

- cmd: `PYTHONPATH=/home/aero/PyProject/ship-sense/apps/edge/collector/src:/home/aero/PyProject/ship-sense/apps/edge/emulator/src pytest -q apps/edge/collector/tests/unit/test_config_validator.py apps/edge/collector/tests/unit/test_mqtt_config.py`
- итог: `8 passed`
- compileall: passed
- lint: `ruff` не установлен в окружении, не запускался

## Integration check

- [x] MQTT protocol added to config validation
- [x] `COLLECTOR_PROFILE` consumed by validator
- [x] publish guard wired at config validation boundary
- [x] map reference consumed and validated
- [x] unknown MQTT fields rejected
- [ ] MQTT connector/registry — следующий s06
