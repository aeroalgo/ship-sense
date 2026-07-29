# Шаг s01: MqttSourceConfig + validation + I1 publish guard
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-01 (partial), AC-MQTT-03

**code_surface:** model

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Pydantic-модели конфигурации MQTT-источника с валидацией и guard subscribe-only (I1): `publish_allowed: false` по умолчанию для prod-профиля.

## Контекст
- **Consumes:** T-001 s02 `SourceConfig`, config loader/validator CLI
- **Produces:** `MqttSourceConfig`, `MqttConnectionConfig`, `MqttSubscribeConfig`; расширение sources.yaml schema для `protocol: mqtt`

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/config.py` (Создание)
- `apps/edge/collector/src/collector/config/models.py` (Модификация — union/discriminator для mqtt)
- `apps/edge/collector/tests/unit/test_mqtt_config.py` (Создание)
- `apps/edge/collector/tests/fixtures/config/mqtt_sources.yaml` (Создание)

## Интерфейсы (lean — без кода)
- model: `MqttConnectionConfig` — поля: host, port, tls, client_id, username, password, ca_cert, client_cert, client_key
- model: `MqttSubscribeConfig` — поля: topic_prefix, qos, shared_subscription
- model: `MqttSourceOptions` — поля: publish_allowed (default false)
- model: `MqttSourceConfig(SourceConfig)` — поля: connection, subscribe, map (path to channel yaml), options
- validator: при `publish_allowed=true` и prod profile env → `ConfigError` (AC-MQTT-03)

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_mqtt_config.py` — parse valid yaml; reject publish in prod; defaults qos=1
2. **Запуск:** тесты падают (моделей нет).
3. **Реализация:** pydantic v2 models + hook в config loader.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Расширить discriminated union `SourceConfig` новым вариантом `protocol='mqtt'`.
2. Зафиксировать proposal defaults из plan §7 (host/port/topic_prefix placeholders).
3. I1 guard: `publish_allowed` assert at config validation, не runtime.
4. CLI validator принимает mqtt sources fixture без ошибок.

## Чекпоинт верификации
- yaml с двумя sources (panel_aps, panel_geu) валидируется
- `publish_allowed: true` + prod flag → ConfigError
- unknown mqtt field → pydantic validation error
