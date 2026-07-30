# Шаг s07: mqtt_channels yaml stub (ship-pack)
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-10 (map lookup), FR-B-MQTT-11

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Stub channel maps для panel_aps и panel_geu: yaml loader + pydantic `MqttChannelMapEntry`; subset aligned with existing tags_stub.

## Контекст
- **Consumes:** T-001 s02 config/map loader patterns; plan §5.3
- **Produces:** `maps/mqtt_channels_aps.yaml`, `maps/mqtt_channels_geu.yaml`, loader module

## Файлы
- `apps/edge/collector/config/maps/mqtt_channels_aps.yaml` (Создание)
- `apps/edge/collector/config/maps/mqtt_channels_geu.yaml` (Создание)
- `apps/edge/collector/src/collector/plugins/mqtt/channel_map.py` (Создание)
- `apps/edge/collector/tests/unit/test_mqtt_channel_map.py` (Создание)

## Интерфейсы (lean — без кода)
- model: `MqttChannelMapEntry` — channel_id, tag_id, kind (analog|discrete|event|egt_group), unit, thresholds.expose
- class: `MqttChannelMap` — lookup(channel_id) → entry | None; load(path)
- yaml schema: channels list per plan §5.3 example

## TDD (красная → зелёная)
1. **Тест:** load stub yaml; known channel_id → tag_id; unknown → None
2. **Запуск:** тесты падают.
3. **Реализация:** pydantic loader + 5–10 stub channels per panel.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Pick subset from tags_stub (APS.TAI4101, APS.DI1401, …) — proposal native_ids.
2. Separate files for aps/geu per plan §7.
3. Validator CLI accepts mqtt sources referencing map paths.
4. Document that final KKS table awaits Канонерка (plan §12 Q6).

## Чекпоинт верификации
- both yaml files load without error
- lookup used by mapper s05 in tests
- kind field drives mapper branch selection
