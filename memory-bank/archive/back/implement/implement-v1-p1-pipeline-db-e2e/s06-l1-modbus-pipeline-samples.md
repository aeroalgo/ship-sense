# [v1-p1-pipeline-db-e2e | s06 | L1 Modbus → samples (AC-PIPE-05)] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s06-l1-modbus-pipeline-samples.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** L1 (test, TDD)  
**Статус:** completed

## Сделано

- Создан `tests/pipeline/test_modbus_pipeline_db.py` (TDD red→green):
  - `@pytest.mark.integration @pytest.mark.slow @pytest.mark.asyncio`
  - `test_modbus_emulator_persists_sample_to_db(writer_endpoint, db_session)` — AC-PIPE-05.
    - Harness: live `ModbusServerAdapter` (TagGenerator profile с native 40101 + 41000) → `ModbusTcpConnector` + passthrough normalizer + `RawConsumer` + `SourceSupervisor` (native ["40101"]) → `IpcCanonicalSink(writer_endpoint)`.
    - Writer: `WriterService.start_tcp("127.0.0.1", 0)` + `writer_loop` (reuse s03 fixture).
    - Poll `SELECT COUNT(*) FROM samples WHERE tag_id IN ('TAI4101', '40101')` до ≥1 или timeout (AssertionError с сообщением, POLL_TIMEOUT_S=30s).
  - Passthrough normalizer `_passthrough_normalize` (align с s03/s04) — B4 нормализация позже.
  - Poll helper `_poll_until()` (reuse pattern из s03/s04).
  - Не мокать `SamplesRepo.insert_batch`.
- TDD:
  - RED: `IndexError: list index of range` в `SimDevice.__check_block` (пустой input_registers блок при профиле без 41xxx сигналов).
  - Fix: добавлен input signal (native "41000", boolean) в profile эмулятора → holding + input registers непустые → `SimDevice` инициализируется.
  - GREEN: `.venv/bin/pytest ...::test_modbus_emulator_persists_sample_to_db -q` → 1 passed (~4.5s).
- Anti-patterns:
  - Нет AsyncMock на insert_batch.
  - Poll с явным AssertionError на timeout (не silent).
  - Реальный Modbus stack (ModbusServerAdapter + ModbusTcpConnector + Supervisor + Consumer), не stub.
- NFR: L1 wall < 60s (типично 4–5s при поднятом эмуляторе).
- AC: AC-PIPE-05 зелёный; AC-PIPE-06 подтверждён косвенно (writer_endpoint от s03).

## Файлы

- `tests/pipeline/test_modbus_pipeline_db.py` (create)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md` (reference)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md`
- `memory-bank/activeContext.md`

## Верификация

- Targeted: `.venv/bin/pytest tests/pipeline/test_modbus_pipeline_db.py::test_modbus_emulator_persists_sample_to_db -q` — **1 passed**.
- Регрессия: не затронуты storage suite / mqtt pipeline тесты (новый файл).
- AC-PIPE-05: Modbus emulator (live TCP) → ModbusTcpConnector + Normalizer + Supervisor + RawConsumer + IpcCanonicalSink → writer → `samples` COUNT≥1 (tag_id 'TAI4101' или native '40101' via passthrough).
- §0.11:
  - `ModbusTcpConnector`, `SourceSupervisor`, `RawConsumer`, `Normalizer`, `IpcCanonicalSink`, `WriterService` — без изменений (только harness использует).
  - `writer_endpoint` fixture — reuse из s03 (WriterService.start_tcp + writer_loop).
  - Tag map: `apps/edge/collector/maps/stub_aps_main.yaml` — без изменений (native 40101 → TAI4101).
  - Emulator: `ModbusServerAdapter` + `TagGenerator` — используется напрямую (как в collector conftest.py `modbus_integration` fixture).
  - Compose writer/db (порт 9009, DATABASE_URL) — не затронуты.
  - Нет правок compose entrypoint / `__main__` / публичного API.
- `code_changed`: yes (тест создан).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.
- AC+: targeted pytest green; AC шага подтверждён (1 тест PASS).
- AC−: не ломать compose/runtime entrypoint и публичный API; не выходить за scope s06 (L1 Modbus→samples, без OPC UA / compose smoke).
- §0.11: все ссылки/ENV/API/entrypoint из diff имеют counterpart (см. выше).
- VERIFY команда: `.venv/bin/pytest tests/pipeline/test_modbus_pipeline_db.py::test_modbus_emulator_persists_sample_to_db -q`.

## Статус

completed (FINISH: step + Handoff в activeContext + decompose flip + load_now на s07)
