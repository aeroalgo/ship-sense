# [v1-p1-pipeline-db-e2e | s03 | L0 IPC frame → samples/events (SQL assert)] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s03-l0-writer-ipc-db.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** L1 (test, TDD)  
**Статус:** completed

## Сделано

- Создан `tests/pipeline/test_writer_ipc_db.py` (TDD red→green):
  - `@pytest.mark.integration @pytest.mark.slow @pytest.mark.asyncio`
  - `test_ipc_sample_persists_to_samples(writer_endpoint, db_session)` — AC-PIPE-01.
    - `IpcCanonicalSink((host, port))`, `connect()`, `write_sample(TelemetrySample)` (tag_id="TAI4101", value=82.5, quality=GOOD, fixed UTC), `flush()`, `close()`.
    - Poll `SELECT COUNT(*) FROM samples WHERE tag_id='TAI4101'` до ≥1 или timeout (AssertionError с сообщением).
    - `pytest.approx(value, abs=1e-6) == 82.5`; `quality == 0` (GOOD).
  - `test_ipc_event_persists_to_events(writer_endpoint, db_session)` — AC-PIPE-02.
    - `write_event(Event)` с `idempotency_key`, `flush()`, `close()`.
    - Poll по `idempotency_key` → COUNT≥1; `event_name` == ожидаемое.
  - Poll helper `_poll_until()` с bounded loop (не fixed sleep), явный `AssertionError` на timeout.
  - Не мокать `SamplesRepo.insert_batch` / `EventsRepo.insert_batch`.
- Исправления в `tests/pipeline/conftest.py` (для L0 green):
  - `alembic upgrade head` в subprocess: `PYTHONPATH` собран явно (`root:collector_src:emulator_src`); используется `.venv/bin/alembic` (не pyenv shim).
  - `timescale_url`: `with_kwargs(shm_size="512m")` (совпадает с compose `shm_size: 512mb`).
  - `timescale_url`: замена `wait_for_logs("database system is ready...")` на bounded poll `pg_isready` внутри контейнера (transient init/shutdown не маскируется).
  - Фикстуры переписаны на `@pytest_asyncio.fixture()` (session-scoped `timescale_url`/`_alembic_migrated`, function-scoped `db_engine`/`db_session`/`writer_endpoint`).
- Исправления в `tests/conftest.py`:
  - `pytest_plugins = ["pytest_asyncio"]` (explicit registration для `asyncio_mode = "strict"` под манипуляцией PYTHONPATH).
- Исправления в `tests/pipeline/test_writer_ipc_db.py`:
  - Добавлены `@pytest.mark.asyncio` на оба теста.
- TDD: тесты писались первыми (red: fixture/AsyncMock/Import/AssertionError) → зелёные после правок.
- Anti-patterns:
  - Нет AsyncMock на `insert_batch` в happy-path.
  - Poll с сообщением при timeout (не silent).
  - Явные ошибки alembic (RuntimeError), не bare except.
- NFR: L0 wall < 30s (session container уже поднят; типично 2–10s).
- AC: AC-PIPE-01 / AC-PIPE-02 зелёные; `AC-PIPE-06` подтверждён косвенно (`start_tcp` используется через `writer_endpoint`).

## Файлы

- `tests/pipeline/test_writer_ipc_db.py` (create)
- `tests/pipeline/conftest.py` (edit: PYTHONPATH/alembic, shm_size, pg_isready poll, pytest_asyncio.fixture)
- `tests/conftest.py` (edit: explicit pytest_asyncio plugin)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md`
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md`
- `memory-bank/activeContext.md`

## Верификация

- Targeted: `.venv/bin/pytest tests/pipeline/test_writer_ipc_db.py -m "integration and slow" -q` — **2 passed**.
- Регрессия: storage suite не затронута (новый пакет).
- AC-PIPE-01: framed IPC sample → row в `samples` (tag_id, value≈, quality=0).
- AC-PIPE-02: framed IPC event → row в `events` (event_name, idempotency_key).
- §0.11:
  - `WriterService.start_tcp` / `writer_loop` / `flush_batches` — не изменены (только harness использует).
  - Compose writer/db (порт 9009, DATABASE_URL, timescale 2.14.2-pg16, shm 512mb) — соответствуют.
  - Alembic 001–006 — без изменений; harness вызывает `alembic upgrade head` с override.
  - Нет правок compose entrypoint / `__main__` / публичного API.
- `code_changed`: yes (тест + фикстуры + conftest для TDD green).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.
- AC+: targeted pytest green; AC шага подтверждён (2 теста PASS).
- AC−: не ломать compose/runtime entrypoint и публичный API; не выходить за scope s03 (L0 IPC→DB, без L1/L2).
- §0.11: все ссылки/ENV/API/entrypoint из diff имеют counterpart (см. выше).
- VERIFY команда: `.venv/bin/pytest tests/pipeline/test_writer_ipc_db.py -m "integration and slow" -q`.

## Статус

completed (FINISH: step + Handoff в activeContext + decompose flip + load_now на s04)
