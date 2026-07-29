# T-008 | s07 | MQTT channel maps stub IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s07-mqtt-channel-maps-stub.md](../../plan/decompose-v1-p1-mqtt/s07-mqtt-channel-maps-stub.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлен Pydantic-контракт `MqttChannelMapEntry` для MQTT channel maps:
  `channel_id`, `tag_id`, `kind`, `unit`, `thresholds.expose`.
- `kind` ограничен поддержанными mapper-ветками: `analog`, `discrete`, `event`, `egt_group`.
- Добавлен `MqttChannelThresholds` с безопасным default `expose=false`.
- Добавлен `MqttChannelMap.load(path)` на базе `yaml.safe_load` и
  `lookup(channel_id) -> MqttChannelMapEntry | None`.
- Дубликаты `channel_id` отклоняются как ошибка карты, неизвестные поля
  отклоняются Pydantic-моделью.
- Добавлены stub ship-pack maps для `panel_aps` и `panel_geu` с subset native IDs
  из существующих `tags_stub`/MQTT fixtures: analog, discrete, event и EGT group.
- Runtime MQTT factory теперь загружает `MqttChannelMap`, а не старый Modbus/OPC
  `TagMapEntry` loader; runtime tag registry строится из channel map entries для
  downstream normalizer.
- Config validator использует MQTT channel-map loader, поэтому YAML с ключом
  `channels` проверяется по MQTT-схеме.
- Экспортированы channel-map типы из `collector.plugins.mqtt`.

## Файлы

- `apps/edge/collector/config/maps/mqtt_channels_aps.yaml`
- `apps/edge/collector/config/maps/mqtt_channels_geu.yaml`
- `apps/edge/collector/src/collector/plugins/mqtt/channel_map.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/src/collector/runtime/bootstrap.py`
- `apps/edge/collector/src/collector/config/validator.py`
- `apps/edge/collector/tests/unit/test_mqtt_channel_map.py`

## TDD

- RED: targeted `test_mqtt_channel_map.py` завершился
  `ModuleNotFoundError: No module named 'collector.plugins.mqtt.channel_map'`.
- GREEN: после добавления модели, loader и YAML maps targeted channel-map tests
  проходят.

## Тесты

- `PYTHONPATH=apps/edge/collector/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_mqtt_channel_map.py apps/edge/collector/tests/unit/test_mqtt_mapper.py apps/edge/collector/tests/unit/test_mqtt_connector.py apps/edge/collector/tests/unit/test_mqtt_config.py apps/edge/collector/tests/unit/test_config_validator.py`
  → **22 passed**.
- `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m compileall -q apps/edge/collector/src/collector/plugins/mqtt/channel_map.py apps/edge/collector/src/collector/runtime/bootstrap.py apps/edge/collector/src/collector/config/validator.py apps/edge/collector/tests/unit/test_mqtt_channel_map.py`
  → **passed**.

## Integration check (§0.11)

- [x] `MqttSemanticMapper._lookup()` принимает `MqttChannelMap` через публичный
  `lookup(channel_id)`.
- [x] `MqttConnector.discover_tags()` продолжает работать через
  `MqttChannelMap.entries`.
- [x] `bootstrap.mqtt_factory()` загружает карту из `MqttSourceConfig.map` и
  передаёт её в connector.
- [x] Runtime normalizer получает `TagMapEntry`-представление MQTT channels,
  включая `native_id=channel_id`, `tag_id`, `kind` и `unit`.
- [x] Validator проверяет MQTT map-файл до старта runtime; duplicate channel IDs
  отклоняются loader-ом.
- [x] Unknown `channel_id` остаётся quarantine-путём mapper, не silent drop.
- [x] Final KKS mapping остаётся stub и ждёт таблицу Канонерки; текущие IDs
  явно обозначены как proposal subset.

## Ограничения / следующий шаг

- Полная KKS/channel table и окончательные APS/GEU native IDs не утверждены;
  карты являются dev/ship-pack stub.
- Existing fixture maps `tests/fixtures/config/maps/mqtt_panel_*.yaml` не заменялись:
  они используются в config-model tests как пустые scaffolds.
- Следующий шаг: [s08-emulator-mqtt-publisher.md](../../plan/decompose-v1-p1-mqtt/s08-emulator-mqtt-publisher.md).
