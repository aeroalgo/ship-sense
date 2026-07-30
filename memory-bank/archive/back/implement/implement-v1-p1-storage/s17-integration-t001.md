# BACK IMPLEMENT s17 — integration T-001

## Scope

Заменить compose writer-stub реальным storage writer, подключить TimescaleDB,
миграции и DB health dependency для collector.

## Changes

- `apps/edge/storage/__main__.py`: production TCP writer entrypoint, Alembic upgrade,
  async PostgreSQL session и semantic pack loading.
- `apps/edge/storage/Dockerfile`: отдельный storage image с runtime dependencies.
- `apps/edge/storage/writer.py`: TCP listener для compose IPC alongside Unix listener.
- `apps/edge/storage/__init__.py`: public exports `SemanticEngine` и `WriterService`.
- `docker-compose.yml`: writer builds storage image, db is healthy dependency, collector
  waits for db and writer, `DATABASE_URL`/`SHIPSSENSE_*` wiring.
- `tests/storage/test_s17_integration.py`: compose wiring and T-003 import gate.

## Verification

```text
PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_s17_integration.py -q
2 passed

PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_writer_batch.py tests/storage/test_s17_integration.py tests/storage/test_semantic_engine.py -q
17 passed
```

## Handoff

- `code_changed`: yes
- `next`: BACK QA
- `blockers`: live `docker compose --profile full up` requires Docker daemon and is not
  run in targeted verification.
