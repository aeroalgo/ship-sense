# Шаг s02: async MQTT client wrapper
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-04, AC-MQTT-05 (partial — transport layer)

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Async обёртка над MQTT-клиентом (aiomqtt): connect, subscribe, on_message callback, reconnect с backoff (reuse T-001 s04 `RestartPolicy` / `compute_backoff`).

## Контекст
- **Consumes:** s01 `MqttSourceConfig`; T-001 s04 restart policy
- **Produces:** `AsyncMqttClient` — transport без semantic parse

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/client.py` (Создание)
- `apps/edge/collector/pyproject.toml` (Модификация — dep `aiomqtt`)
- `apps/edge/collector/tests/unit/test_mqtt_client.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `AsyncMqttClient` — поля: config, on_message callback
- methods: connect, disconnect, subscribe(topic_filter, qos), is_connected
- callback: `OnMqttMessage(topic, payload: bytes, recv_ts)` — async или sync dispatch в connector
- errors: `MqttConnectionError`, `MqttSubscribeError` — typed, не глотают loop
- reconnect: backoff через shared `compute_backoff`; duplicate connect idempotent

## TDD (красная → зелёная)
1. **Тест:** mock broker / aiomqtt test double — connect+subscribe; reconnect after disconnect; malformed transport не crash client task
2. **Запуск:** тесты падают.
3. **Реализация:** aiomqtt Client wrapper + asyncio task lifecycle.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Добавить `aiomqtt` в collector dependencies (plan §6).
2. Wrapper не парсит JSON — только bytes + topic + timestamp.
3. Subscribe-only: wrapper **не** экспортирует publish API (I1 на уровне connector/config).
4. Reconnect loop отделён от parse/mapper (connector s06 соберёт).

## Чекпоинт верификации
- subscribe вызывается с topic_prefix из config
- disconnect → auto reconnect с backoff
- on_message callback invoked без блокировки event loop > smoke threshold
