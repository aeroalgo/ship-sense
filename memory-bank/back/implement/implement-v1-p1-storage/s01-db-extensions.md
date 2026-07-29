# [v1-p1-storage | s01 | db-extensions] IMPLEMENT

**Plan ID:** v1-p1-storage  
**Decompose step:** [s01-db-extensions.md](../../plan/decompose-v1-p1-storage/s01-db-extensions.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-29  
**Уровень:** L1 (DDL baseline, без runtime-кода)  
**Статус:** done

## Сделано

- Создан минимальный `alembic.ini` с `migrations` как script location и PostgreSQL URL по умолчанию.
- Создан `migrations/env.py` для online/offline режимов SQLAlchemy 2/Alembic с `DATABASE_URL` override и `include_schemas=True`.
- Создана revision `001_extensions_timescale`:
  - включает `timescaledb` и `uuid-ossp` через `CREATE EXTENSION IF NOT EXISTS`;
  - создаёт схему `shipsense`;
  - устанавливает `search_path` текущей Alembic-сессии в `shipsense, public`.
- `downgrade()` удаляет схему `shipsense` с `CASCADE` согласно контракту шага.

## Файлы

- `alembic.ini`
- `migrations/env.py`
- `migrations/versions/001_extensions_timescale.py`
- `memory-bank/back/plan/decompose-v1-p1-storage/index.md`
- `memory-bank/activeContext.md`

## Верификация

- `.venv/bin/alembic history` — PASS: `<base> -> 001_extensions_timescale (head)`.
- `.venv/bin/alembic heads` — PASS: `001_extensions_timescale (head)`.
- `.venv/bin/alembic upgrade head --sql` — PASS: сгенерирован ожидаемый DDL.
- `.venv/bin/alembic downgrade 001_extensions_timescale:base --sql` — PASS: сгенерирован ожидаемый `DROP SCHEMA IF EXISTS shipsense CASCADE`.
- `.venv/bin/alembic current` — блокировано отсутствием доступной PostgreSQL на `localhost:5432` (конфигурация по умолчанию).
- `alembic upgrade head` / реальный `downgrade -1` не запускались без TimescaleDB dev instance.
- `.venv/bin/pytest` не запускался: шаг чистый DDL, тестовые файлы отсутствуют.

## Review

Read-only review: PASS с замечаниями, не блокирующими AC. `SET search_path` действует для текущей миграционной сессии, что соответствует интерфейсу shard; downgrade намеренно удаляет только схему по заданному контракту.

## Handoff

Следующий шаг: BACK IMPLEMENT s02-samples-hypertable.

- `code_changed: yes`
- Graphify обновлён после изменений: `.venv/bin/graphify update .`
- Для полноценной проверки требуется TimescaleDB PostgreSQL 16 (`timescaledb:2.14.2-pg16`), затем `alembic upgrade head`, `alembic downgrade -1` и повторный upgrade.
