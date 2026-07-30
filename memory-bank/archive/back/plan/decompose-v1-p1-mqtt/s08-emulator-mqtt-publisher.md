# Шаг s08: I3 MQTT publisher emulator adapter
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-30, AC-MQTT-31 (publisher side)

- **Creative (soft):** CR-COL-05b / CR-COL-03 transport separation — I3 не притворяется Modbus

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
I3 adapter: publish 4 message types по stub channels @ ~1 Hz; deterministic lifecycle transitions (seed); отдельный transport от Modbus/OPC (CR-COL-03).

## Контекст
- **Consumes:** s03 payload shape (stub/proposal until CR-COL-05); T-001 s15 TagGenerator optional for correlated values; s07 channel ids
- **Produces:** `MqttPublisherAdapter` in emulator process

## Файлы
- `apps/edge/emulator/src/emulator/protocols/mqtt_publisher.py` (Создание)
- `apps/edge/emulator/tests/test_mqtt_publisher.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `MqttPublisherAdapter` — connect(broker_url), publish_loop, stop
- method: build JSON payloads matching s03 models (proposal enums)
- topics: `shipsense/v1/{panel}/{kind}/{channel_id}` per [CR-COL-05 creative](../../creative/v1-p1-mqtt/creative-collector-mqtt-contract.md)
- deterministic: fixed seed → same lifecycle sequence (AC-MQTT-31)
- ScenarioRunner hook: post T-001 s18 for dirt (optional extension, not blocking)

## TDD (красная → зелёная)
1. **Тест:** mock broker receives analog+discrete messages; seed reproducibility; obeys topic prefix
2. **Запуск:** тесты падают.
3. **Реализация:** aiomqtt or paho publisher in emulator package.
4. **Запуск:** tесты проходят.

## Подробный процесс выполнения
1. Publish-only adapter (dev); не reuse Modbus register mapping.
2. Two panel profiles: aps vs geu topic_prefix.
3. Synthetic lifecycle transitions on timer (deterministic PRNG).
4. Rewire after CR-COL-05 if topic taxonomy changes.

## Чекпоинт верификации
- publishes all 4 payload kinds
- same seed → identical event sequence count
- transport separation: no modbus/opc imports in mqtt_publisher module
