# Шаг s04: L1 MQTT publisher → collector stack → samples
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-PIPE-03
**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Полный Contour A in-proc: MQTT publish → Mosquitto (testcontainers/reuse) → `MqttConnector`+Normalizer+Supervisor → `IpcCanonicalSink` → writer → `samples.tag_id='TAI4101'` COUNT≥1; value ≈ payload.

## Контекст
- **Consumes:** s02/s03 fixtures; pattern `apps/edge/collector/tests/integration/test_mqtt_e2e.py` (MockSink → заменить на IPC); channel maps `mqtt_channels_*.yaml`; `MqttPublisherAdapter` или aiomqtt publish fixture.
- **Produces:** `tests/pipeline/test_mqtt_pipeline_db.py` (analog path).

## Файлы
- `tests/pipeline/test_mqtt_pipeline_db.py` (Создание)
- `tests/pipeline/conftest.py` (Модификация — mqtt_broker fixture reuse/wrap если ещё нет)

## Интерфейсы (lean — без кода)
- Harness: connector + RawConsumer + Normalizer + SourceSupervisor + RestartPolicy; sink=`IpcCanonicalSink(writer_endpoint)`.
- Publish: APS.TAI4101 analog (или `MqttPublisherAdapter(panel="aps", iterations=2..3)`).
- Assert: `SELECT count(*) FROM samples WHERE tag_id='TAI4101'` ≥ 1; value approx.
- Markers: `integration`, `slow` (+ optional `e2e` если уже в pyproject).
- Default без ship-pack quarantine (`quarantined_tags=None`).

## TDD (красная → зелёная)
1. **Тест:** `test_mqtt_emulator_persists_analog_to_db` — скелет plan §9.2; red до wiring.
2. **Реализация:** wire как e2e MQTT, sink=IPC.
3. **Запуск:** `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py::test_mqtt_emulator_persists_analog_to_db -q` PASS.

## Подробный процесс выполнения
1. Поднять mosquitto fixture (не дублировать ломающие quirks collector package — prefer local wrap).
2. Start supervisor + writer; publish N iterations.
3. Poll SQL до timeout; fail-loud.
4. Не трогать production framing.

## Чекпоинт верификации
- AC-PIPE-03: TAI4101 в samples.
- FR-1, FR-2.

## Зависимости
- s01–s03; T-008 mqtt e2e pattern.

## Frontend
N/A. Docker — parent.

## Следующий шаг
→ s05 (lifecycle → events).
