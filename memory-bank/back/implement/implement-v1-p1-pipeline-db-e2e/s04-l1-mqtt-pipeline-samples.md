# [v1-p1-pipeline-db-e2e | s04 | L1 MQTT → samples (AC-PIPE-03)] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s04-l1-mqtt-pipeline-samples.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** L1 (test, TDD)  
**Статус:** completed

## Сделано

- Создан `tests/pipeline/test_mqtt_pipeline_db.py` (TDD red→green):
  - `@pytest.mark.integration @pytest.mark.slow @pytest.mark.asyncio`
  - `test_mqtt_emulator_persists_analog_to_db(mqtt_broker, writer_endpoint, db_session)` — AC-PIPE-03.
    - Harness: MqttChannelMap.load(APS_MAP) → TagMapEntry conversion (matching collector e2e pattern) → Normalizer.from_yaml → RawConsumer → MqttConnector + SourceSupervisor (tag "APS.TAI4101") → IpcCanonicalSink(writer_endpoint).
    - Publish: aiomqtt.Client → topic `shipsense/v1/aps/analog/APS.TAI4101` с payload из `analog.json` (value=82.5), 3 итерации.
    - Poll `SELECT COUNT(*) FROM samples WHERE tag_id='TAI4101'` до ≥1 или timeout (AssertionError с сообщением, POLL_TIMEOUT_S=30s).
    - Verify: `pytest.approx(value, abs=0.01) == 82.5` на последней строке.
  - Passthrough normalizer `_passthrough_normalize` (align с s03) — B4 нормализация позже.
  - Poll helper `_poll_until()` (reuse pattern из s03, увеличенный timeout).
  - Не мокать `SamplesRepo.insert_batch` / `EventsRepo.insert_batch`.
- TDD:
  - RED: `AssertionError: timeout ... last_count=0` (до wiring + до TagMapEntry fix).
  - Fix: `AttributeError: 'MqttChannelMapEntry' object has no attribute 'range_min'` → конверсия entry → TagMapEntry (native_id, tag_id, datatype, unit) как в `collector/tests/integration/test_mqtt_e2e.py::_normalizer`.
  - GREEN: `.venv/bin/pytest ...::test_mqtt_emulator_persists_analog_to_db -q` → 1 passed (~5s).
- Anti-patterns:
  - Нет AsyncMock на insert_batch.
  - Poll с явным AssertionError на timeout (не silent).
  - Реальный collector stack (MqttConnector/Supervisor/Consumer/Normalizer), не stub.
- NFR: L1 wall < 60s (типично 5–10s при поднятом mosquitto).
- AC: AC-PIPE-03 зелёный; AC-PIPE-06 подтверждён косвенно (writer_endpoint от s03).

## Файлы

- `tests/pipeline/test_mqtt_pipeline_db.py` (create)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md` (reference)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md`
- `memory-bank/activeContext.md`

## Верификация

- Targeted: `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py::test_mqtt_emulator_persists_analog_to_db -q` — **1 passed**.
- Регрессия: не затронуты storage suite / collector mqtt e2e (новый пакет pipeline).
- AC-PIPE-03: MQTT publish → mosquitto → collector stack (MqttConnector+Normalizer+Supervisor+IpcCanonicalSink) → writer → `samples.tag_id='TAI4101'` COUNT≥1; value≈82.5.
- §0.11:
  - `MqttConnector`, `SourceSupervisor`, `RawConsumer`, `Normalizer`, `IpcCanonicalSink`, `WriterService` — без изменений (только harness использует).
  - `mqtt_broker` fixture (testcontainers MosquittoContainer) — в `tests/pipeline/conftest.py` (local wrap collector pattern, из s02).
  - `writer_endpoint` fixture — reuse из s03 (WriterService.start_tcp + writer_loop).
  - Channel maps / fixtures: `apps/edge/collector/config/maps/mqtt_channels_aps.yaml`, `apps/edge/collector/tests/fixtures/mqtt/analog.json` — без изменений.
  - Compose writer/db (порт 9009, DATABASE_URL) — не затронуты.
  - Нет правок compose entrypoint / `__main__` / публичного API.
- `code_changed`: yes (тест создан).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.
- AC+: targeted pytest green; AC шага подтверждён (1 тест PASS).
- AC−: не ломать compose/runtime entrypoint и публичный API; не выходить за scope s04 (L1 MQTT→samples, без lifecycle events / modbus).
- §0.11: все ссылки/ENV/API/entrypoint из diff имеют counterpart (см. выше).
- VERIFY команда: `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py::test_mqtt_emulator_persists_analog_to_db -q`.

## Статус

completed (FINISH: step + Handoff в activeContext + decompose flip + load_now на s05)
