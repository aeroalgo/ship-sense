# Шаг s09: integration E2E — mosquitto + collector
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-30, AC-MQTT-02 (integration)

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Integration test: mosquitto (testcontainer or fixture broker) + s08 publisher or inline publish + collector mqtt source → MockSink receives TelemetrySample/Event.

## Контекст
- **Consumes:** s06 connector, s08 publisher (or inline fixture publish), s03 fixtures
- **Produces:** `tests/integration/test_mqtt_e2e.py`

## Файлы
- `apps/edge/collector/tests/integration/test_mqtt_e2e.py` (Создание)
- `apps/edge/collector/tests/conftest.py` (Модификация — mqtt broker fixture if needed)

## Интерфейсы (lean — без кода)
- fixture: `mqtt_broker` — ephemeral port, teardown
- test: publish analog fixture → collector running → MockSink.samples non-empty
- test: dual source configs → both panels produce samples

## TDD (красная → зелёная)
1. **Тест:** E2E message → canonical sample in MockSink
2. **Запуск:** тесты падают (wire incomplete).
3. **Реализация:** integration harness per python-testing-patterns testcontainer pattern.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Prefer testcontainers mosquitto OR docker-compose test profile if project already uses one pattern (grep sibling s19).
2. Start collector with mqtt-only sources yaml pointing at test broker.
3. Publish golden JSON from `tests/fixtures/mqtt/`.
4. Assert tag_id, value, event lifecycle on transition fixture.

## Чекпоинт верификации
- AC-MQTT-30 satisfied
- regression: T-001 modbus/opc tests unchanged when running full suite
- test marked integration/slow if needed in pyproject markers
