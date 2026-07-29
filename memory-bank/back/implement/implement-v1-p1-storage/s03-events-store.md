# [v1-p1-storage | s03 | events-store] IMPLEMENT

**Plan ID:** v1-p1-storage  
**Decompose step:** [s03-events-store.md](../../plan/decompose-v1-p1-storage/s03-events-store.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-29  
**Уровень:** L1 (DDL migration)  
**Статус:** done

## Сделано

- Создана revision `003_events_append_only` поверх `002_samples_hypertable`.
- Создана таблица `events` с UUID PK, unique `idempotency_key`, временной осью, JSONB `params`, `severity` check и `reconstructed` default `FALSE`.
- Добавлены индексы для official time, event name, source, `params->>'tag_id'` и lifecycle alarm-фильтра.
- Добавлены функция `forbid_events_mutation()` и BEFORE UPDATE OR DELETE trigger для append-only режима.
- Downgrade удаляет таблицу и функцию; core schema остаётся frozen, dual-mode поддерживается через `reconstructed` и JSONB params.

## Файлы

- `migrations/versions/003_events_append_only.py`
- `memory-bank/back/implement/implement-v1-p1-storage/index.md`
- `memory-bank/activeContext.md`

## Верификация

- `.venv/bin/python -m py_compile migrations/versions/003_events_append_only.py` — PASS.
- `.venv/bin/alembic history` — PASS: `002_samples_hypertable -> 003_events_append_only (head)`.
- `.venv/bin/alembic upgrade head --sql` — PASS: полный offline SQL сформирован.
- `.venv/bin/alembic upgrade 002_samples_hypertable:003_events_append_only --sql` — PASS: SQL events upgrade сформирован.
- `.venv/bin/alembic downgrade 003_events_append_only:002_samples_hypertable --sql` — PASS: SQL events downgrade сформирован.
- Реальная проверка PostgreSQL duplicate key, UPDATE/DELETE trigger и EXPLAIN не запускалась: доступная проверка выполнена в offline-режиме.
