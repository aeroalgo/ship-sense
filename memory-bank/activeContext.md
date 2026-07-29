## load_now
1. `memory-bank/back/plan/decompose-v1-p1-storage/s07-events-repo.md` — next shard BACK IMPLEMENT s07-events-repo

## Handoff BACK IMPLEMENT s01

- **Предыдущий:** BACK DECOMPOSE v1-p1-storage
- **Следующий:** BACK IMPLEMENT s02-samples-hypertable
- **Кратко:** Создана минимальная Alembic-конфигурация (alembic.ini, env.py) и первая миграция `001_extensions_timescale` для включения расширений `timescaledb` и `uuid-ossp`, а также создания схемы `shipsense`.
- **code_changed:** yes
- **New chat:** no

## Handoff BACK IMPLEMENT s02

- **Предыдущий:** BACK IMPLEMENT s02-samples-hypertable
- **Следующий:** BACK IMPLEMENT s03-events-store
- **Кратко:** Создана Alembic revision `002_samples_hypertable` поверх `001_extensions_timescale`: таблица `samples`, PK `(tag_id, ts)`, quality check 0–5, hypertable по `ts` с chunk interval 1 day и три требуемых индекса.
- **code_changed:** yes
- **Верификация:** `.venv/bin/alembic history`, `upgrade head --sql`, `downgrade 002_samples_hypertable:001_extensions_timescale --sql` — PASS; реальный SQL against DB не запускался.
- **New chat:** no

## Сейчас
BACK CREATIVE CR-STO-04 завершён. Следующий шаг — BACK IMPLEMENT s07-events-repo.

## Следующий шаг
1. BACK IMPLEMENT s07-events-repo по [creative-event-dual-mode-schema.md](back/creative/creative-event-dual-mode-schema.md).

## Handoff BACK CREATIVE CR-STO-04

- **Предыдущий:** BACK IMPLEMENT s06-samples-repo
- **Следующий:** BACK IMPLEMENT s07-events-repo
- **Кратко:** Зафиксирована схема `frozen core + JSONB domain envelope` для native/reconstructed событий, модели `AlarmEventParamsQ4A/B`, invariant-проверки и режимы `auto|native|reconstruct`.
- **code_changed:** no
- **Creative:** [creative-event-dual-mode-schema.md](back/creative/creative-event-dual-mode-schema.md)

## Handoff BACK IMPLEMENT s04

- **Предыдущий:** BACK IMPLEMENT s04-meta-health-tables
- **Следующий:** BACK IMPLEMENT s05-sqlalchemy-models
- **Кратко:** Созданы Alembic revisions `004_time_semantic_health` и `005_quota_degrade` с таблицами clock shift, semantic metadata, quarantine, health snapshots, quota config, degradation log и watermark stub; добавлен seed 8 TiB.
- **Верификация:** `py_compile`, `.venv/bin/alembic history`, `.venv/bin/alembic upgrade head --sql`, offline downgrade — PASS; live PostgreSQL не запускался.
- **code_changed:** yes
- **New chat:** no

## Handoff BACK IMPLEMENT s03

- **Предыдущий:** BACK IMPLEMENT s03-events-store
- **Следующий:** BACK IMPLEMENT s04-meta-health-tables
- **Кратко:** Создана Alembic revision `003_events_append_only` поверх `002_samples_hypertable`: append-only таблица `events`, idempotency UNIQUE, JSONB params, severity check, временная ось, индексы для journal/correlation и trigger запрета UPDATE/DELETE.
- **Верификация:** py_compile, `alembic history`, offline upgrade head, offline events upgrade/downgrade — PASS; реальный PostgreSQL trigger/duplicate/EXPLAIN не запускался.
- **code_changed:** yes
- **New chat:** no

## Блокеры
- CREATIVE CR-STO-01/02 (s16); CR-STO-03/04 (s13/s15, s07 validators).
- T-001 canonical/IPC финализация до s17.
- Ф0 native map (stub в s14 ok).

## Версии
- v1 ship: phase 1 → phase 2
- v2 shore: after v1

## done — do NOT load
- BACK DECOMPOSE v1-p1-storage 2026-07-29
- BACK QA v1-p1-mqtt-smoke 2026-07-29 (completed)
- BACK IMPLEMENT v1-p1-mqtt-smoke s07 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s06 2026-07-29
- BACK BUGFIX mqtt-smoke-emulator-entrypoint 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s05 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s04 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s03 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s02 2026-07-29
- BACK IMPLEMENT v1-p1-mqtt-smoke s01 2026-07-29
- BACK DECOMPOSE v1-p1-mqtt-smoke 2026-07-29
