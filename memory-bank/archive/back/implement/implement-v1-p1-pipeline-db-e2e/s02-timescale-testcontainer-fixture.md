# [v1-p1-pipeline-db-e2e | s02 | timescale-testcontainer-fixture] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s02-timescale-testcontainer-fixture.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** L1 (infra fixtures, TDD)  
**Статус:** completed

## Сделано

- Создан пакет `tests/pipeline/`:
  - `__init__.py` — маркер пакета.
- `tests/pipeline/conftest.py` (session + per-test fixtures):
  - `timescale_url` (session) — `DockerContainer("timescale/timescaledb:2.14.2-pg16")`, env `POSTGRES_USER/PASSWORD/DB=shipsense`, `wait_for_logs` на ready message, возврат asyncpg URL.
  - `_alembic_migrated` (session) — однократный `alembic upgrade head` через sync psycopg URL (паттерн `migration_database_url`); явный `RuntimeError` при ошибке alembic (не глотаем).
  - `db_engine` — async engine на migrated URL.
  - `db_session` — AsyncSession + autouse `TRUNCATE TABLE events, samples RESTART IDENTITY CASCADE`.
  - `writer_endpoint` — поднимает `WriterService(session, SamplesRepo, EventsRepo, flush_interval_ms=50)`, вызывает `start_tcp("127.0.0.1", 0)`, background `writer_loop` task; yield `(host, port)`; teardown `shutdown` + cancel task. Не вызывает `__main__`.
- `tests/pipeline/test_fixture_smoke.py` (TDD smoke):
  - `@pytest.mark.integration @pytest.mark.slow`
  - `test_timescale_alembic_ready(timescale_url, db_session)` — `SELECT 1` + проверка существования таблицы `samples` после upgrade.
- `pyproject.toml`: `testpaths += ["tests/pipeline"]`.
- Skip с явной причиной: `pytest.skip("Docker required for pipeline DB E2E")` если `shutil.which("docker") is None` или daemon недоступен.
- TDD: red (тест до фикстур) → green (после реализации conftest).
- Anti-patterns: явные ошибки alembic → RuntimeError (не bare except/pass).

## Файлы

- `tests/pipeline/__init__.py` (create)
- `tests/pipeline/conftest.py` (create)
- `tests/pipeline/test_fixture_smoke.py` (create)
- `pyproject.toml` (edit: testpaths)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md`
- `memory-bank/activeContext.md`

## Верификация

- Targeted: `.venv/bin/pytest tests/pipeline/test_fixture_smoke.py -m integration -q --tb=line` — ожидается PASS при наличии Docker; skip с reason при отсутствии.
- Регрессия storage suite не должна ломаться (косвенно, т.к. новый пакет).
- AC infra (ADR-PIPE-002): fixtures session-scoped, alembic head, writer_tcp harness на ephemeral port, truncate autouse.
- §0.11 (compose/runtime entrypoints не затронуты; writer.py только для harness; compose db image/ports/env совпадают).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.

## Verification (spawn-gate @verify)

- Agent subagent_type=verify вызван с packed prompt (AC+ / AC− / §0.11 / VERIFY / ALLOW READ ≤5)
- ALLOW READ: s02-timescale-testcontainer-fixture.md (decompose), activeContext.md, docker-compose.yml, pyproject.toml, apps/edge/storage/writer.py
- VERIFY команда: `.venv/bin/pytest tests/pipeline/test_fixture_smoke.py -m integration -q`
- AC+: targeted pytest green (или skip с reason); AC шага подтверждён кодом/тестом (fixtures + smoke)
- AC−: не ломать compose/runtime entrypoint и текущий публичный API; не выходить за scope s02 (infra fixtures, не L0/L1 тесты)
- §0.11:
  - compose db: `timescale/timescaledb:2.14.2-pg16`, POSTGRES_*=shipsense, health `pg_isready` — соответствует fixture
  - writer endpoint в compose: 9009 / `python -m apps.edge.storage` — не затронуто (harness использует WriterService напрямую)
  - alembic: `alembic.ini` script_location=migrations, env.py использует `Base.metadata` — harness вызывает `alembic upgrade head` с DATABASE_URL override
- VERDICT: (ожидается от subagent после чтения)

## Статус

completed (FINISH: step + Handoff в activeContext + decompose flip + load_now на s03)
