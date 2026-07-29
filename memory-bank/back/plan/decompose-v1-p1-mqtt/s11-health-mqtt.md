# Шаг s11: Health snapshot — mqtt source fields
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-40

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Extend health snapshot per mqtt source: connected, subscribed, last_msg_ts, parse_errors, broker reachability.

## Контекст
- **Consumes:** T-001 s14 HealthAggregator; s06 connector metrics
- **Produces:** mqtt section in health JSON schema

## Файлы
- `apps/edge/collector/src/collector/health/aggregator.py` (Модификация)
- `apps/edge/collector/src/collector/plugins/mqtt/connector.py` (Модификация — healthcheck payload)
- `apps/edge/collector/tests/unit/test_health_mqtt.py` (Создание)

## Интерфейсы (lean — без кода)
- method: `MqttConnector.healthcheck() → dict` — subscribed, connected, last_msg_ts, parse_errors
- aggregator: merge mqtt source health under sources[id].protocol=mqtt
- snapshot: JSON file shape backward compatible with s14

## TDD (красная → зелёная)
1. **Тест:** mock connector states → snapshot contains mqtt fields; parse_errors increment reflected
2. **Запуск:** tесты падают.
3. **Реализация:** wire connector metrics to aggregator.
4. **Запуск:** tесты проходят.

## Подробный процесс выполнения
1. Reuse BaseSourceConnector health patterns from modbus/opcua.
2. `last_msg_ts` ISO8601 or unix ms — match s14 convention.
3. subscribed=false when reconnect in progress but not fatal.

## Чекпоинт верификации
- AC-MQTT-40 fields present in snapshot JSON
- existing modbus health tests still pass
