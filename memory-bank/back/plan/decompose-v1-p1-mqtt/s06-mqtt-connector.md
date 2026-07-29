# Шаг s06: MqttConnector + PluginRegistry
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-COL-05) — **closed** | **tdd:** yes
**AC:** AC-MQTT-01, AC-MQTT-02, AC-MQTT-04, AC-MQTT-05

- **Creative:** [CR-COL-05 / creative-collector-mqtt-contract.md](../../creative/creative-collector-mqtt-contract.md) — subscribe `shipsense/v1/{panel}/#`, broker topology edge-side prod

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
`MqttConnector(BaseSourceConnector)` — protocol=`mqtt`; on_message → parse → map → raw_queue; register в PluginRegistry; два источника изолированы через T-001 supervisor.

## Контекст
- **Consumes:** s01–s05; T-001 s03 PluginRegistry, s04 SourceSupervisor, s05 queues
- **Produces:** working mqtt plugin; `PluginRegistry.create('mqtt', config)`

## Файлы
- `apps/edge/collector/src/collector/plugins/mqtt/connector.py` (Создание)
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py` (Создание)
- `apps/edge/collector/src/collector/plugins/registry.py` (Модификация — register mqtt)
- `apps/edge/collector/tests/unit/test_mqtt_connector.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `MqttConnector(BaseSourceConnector)` — protocol `mqtt`
- methods: connect (start client), subscribe (native MQTT push), read (last-value cache optional), disconnect, healthcheck
- on_message pipeline: bytes → parse_mqtt_payload → mapper → on_sample callback / raw queue put
- metrics: parse_errors, messages_received, last_msg_ts
- register: `@PluginRegistry.register('mqtt')` or explicit register at startup

## TDD (красная → зелёная)
1. **Тест:** create('mqtt') returns connector; mock client message → RawSample in callback; malformed JSON → parse_errors++, connector alive; two connector instances independent
2. **Запуск:** тесты падают.
3. **Реализация:** wire s02 client + s03–s05 semantic stack.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. `read()` — optional health/diagnostics cache (FR-B-MQTT-8); primary path = subscribe push.
2. Parse error handling: increment metric, log, continue (FR-B-MQTT-9).
3. No publish path exposed (I1 enforced at config + no client API).
4. Entrypoint/collector startup registers mqtt alongside modbus/opcua.

## Чекпоинт верификации
- AC-MQTT-01: PluginRegistry.create('mqtt') works
- AC-MQTT-02: two configs → two connectors, failure isolation (unit/mock level)
- AC-MQTT-05: bad JSON does not kill connector task
