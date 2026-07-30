## load_now
1. `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md` — следующий шаг после s05

## Handoff BACK IMPLEMENT T-002 s03

- **Предыдущий:** [s02-timescale-testcontainer-fixture.md](memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md) — done
- **Следующий:** [s04-l1-mqtt-pipeline-samples.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md)
- **Кратко:** L0 IPC framed → DB rows без моков repos. `tests/pipeline/test_writer_ipc_db.py`: `test_ipc_sample_persists_to_samples` (AC-PIPE-01) и `test_ipc_event_persists_to_events` (AC-PIPE-02) — оба PASSED. `IpcCanonicalSink` → `WriterService.start_tcp` + `writer_loop` + `flush_batches` → `samples`/`events` с COUNT≥1, value≈, quality=0. Poll bounded loop с AssertionError на timeout. TDD red→green. Фиксы: `pytest_asyncio.fixture()`, `pg_isready` poll вместо `wait_for_logs`, `PYTHONPATH` + `.venv/bin/alembic` для subprocess alembic, `with_kwargs(shm_size="512m")`, `tests/conftest.py` explicit `pytest_plugins=["pytest_asyncio"]`. code_changed=yes.
- **Артефакт:** memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md
- **Верификация:** `.venv/bin/pytest tests/pipeline/test_writer_ipc_db.py -m "integration and slow" -q` → 2 passed. AC-PIPE-01/02 green; нет AsyncMock на insert_batch; compose/runtime entrypoint и публичный API writer не затронуты.
- **code_changed:** yes
- **graphify:** требуется из корня репо: `.venv/bin/graphify update .` (после FINISH)
- **New chat:** yes (context economy, epic mode — один шаг за сессию)

## Handoff BACK QA T-002 v1-p1-storage (re-QA PASS)
- **Предыдущий:** BACK BUGFIX T-002 qa-storage-runtime — [bugfix-20260730](../bugfix/bugfix-20260730-qa-storage-runtime.md) — completed
- **Следующий:** `BACK IMPLEMENT` — s01-writer-start-tcp из decompose-v1-p1-pipeline-db-e2e
- **Кратко:** re-QA после bugfix → VERDICT: PASS. Storage suite 67 passed; full suite 400 passed (EXIT:0); runtime logs clean (ModbusException=0); live DB data flowing (>200k samples, >4k events); все AC+/AC−/§0.11 подтверждены; reviewer: Agent→reviewer.
- **Артефакт:** `memory-bank/back/qa/qa-20260730-v1-p1-storage-reqa.md`
- **Верификация:** targeted + full pytest 400 passed; compose services healthy; DB tables/counts verified; runtime logs без ModbusException
- **code_changed:** no (re-QA, без новых правок)
- **New chat:** yes (context economy)

## Handoff BACK BUGFIX T-002 qa-storage-runtime
- **Предыдущий:** BACK QA storage — [qa-20260730](memory-bank/back/qa/qa-20260730-v1-p1-storage.md) — blocked
- **Следующий:** `BACK QA` — повторный QA storage/full suite после BUGFIX
- **Кратко:** ModbusException → bad quality + runtime map ⊆ emulator; compression `if_not_exists`; mqtt_broker start timeout 60s. Full suite 400 passed ~79s; live collector logs без ModbusException.
- **Артефакт:** `memory-bank/back/bugfix/bugfix-20260730-qa-storage-runtime.md`
- **Верификация:** targeted + full pytest 400 passed; compose collector rebuild healthy
- **code_changed:** yes
- **New chat:** yes

## Handoff BACK IMPLEMENT T-002 s04

- **Предыдущий:** [s03-l0-writer-ipc-db.md](memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md) — done
- **Следующий:** [s05-l1-mqtt-lifecycle-events.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md)
- **Кратко:** L1 MQTT: publisher → mosquitto (testcontainers) → collector stack (MqttConnector+Normalizer+SourceSupervisor+IpcCanonicalSink) → writer → `samples.tag_id='TAI4101'` COUNT≥1, value≈82.5. `tests/pipeline/test_mqtt_pipeline_db.py`: `test_mqtt_emulator_persists_analog_to_db` (AC-PIPE-03) — PASSED. TDD red→green. Fix: TagMapEntry conversion (MqttChannelMapEntry → native_id/tag_id/datatype/unit) вместо передачи entry напрямую (AttributeError range_min). Poll bounded loop + AssertionError на timeout. Не мокать repos. code_changed=yes.
- **Артефакт:** memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md
- **Верификация:** `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py::test_mqtt_emulator_persists_analog_to_db -q` → 1 passed. AC-PIPE-03 green; compose/runtime entrypoint и публичный API не затронуты.
- **code_changed:** yes
- **graphify:** требуется из корня реpo: `.venv/bin/graphify update .` (после FINISH)
- **New chat:** yes (context economy, epic mode — один шаг за сессию)

## Handoff BACK IMPLEMENT T-002 s05

- **Предыдущий:** [s04-l1-mqtt-pipeline-samples.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md) — done
- **Следующий:** [s06-l1-modbus-pipeline-samples.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md)
- **Кратко:** AC-PIPE-04 зелёный. L1 MQTT lifecycle (exceeded) → `events` с `event_name='aps.threshold.exceeded'`, COUNT≥1. TDD red→green. `MqttConnector(on_event=sink.write_event)` + `IpcCanonicalSink` + `WriterService` → DB. Poll bounded. s04 регрессия зелёная. code_changed=yes.
- **Артефакт:** `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md`
- **Верификация:** `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py -q` → оба теста PASSED. AC-PIPE-04 green; compose/runtime entrypoint и публичный API writer не затронуты.
- **code_changed:** yes
- **graphify:** требуется из корня реpo: `.venv/bin/graphify update .` (после FINISH)
- **New chat:** yes (context economy, epic mode — один шаг за сессию)

## done — do NOT load
- `memory-bank/back/bugfix/bugfix-20260729-package-path-compose-runtime.md`
- `memory-bank/back/qa/qa-20260729-v1-p1-storage.md`
- `memory-bank/back/implement/implement-v1-p1-storage/` — s01–s18 done
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/` — Handoff DECOMPOSE снят; s01–s04 done, s05 ждёт IMPLEMENT
