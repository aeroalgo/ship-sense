# [T-002 | s04 | meta-health-tables] IMPLEMENT
**Plan ID:** v1-p1-storage
**Decompose step:** [s04-meta-health-tables.md](../../plan/decompose-v1-p1-storage/s04-meta-health-tables.md)
**Дата:** 2026-07-29
**Уровень:** L2 (Alembic SQL migrations)
**AC:** AC-STO-S04
**Статус:** done

## Сделано

- Создана revision `004_time_semantic_health` поверх `003_events_append_only`:
  `clock_shift_log`, `semantic_meta`, `tag_quarantine`, `health_snapshots` и индексы по временным полям.
- Создана revision `005_quota_degrade` поверх `004_time_semantic_health`:
  `storage_quota_config`, `samples_degrade_log`, `samples_degrade_watermark` и индекс журнала деградации.
- Добавлен seed `storage_quota_config.disk_total_bytes = 8589934592000` с `ON CONFLICT DO NOTHING`.
- Downgrade удаляет таблицы в обратном порядке зависимостей.

## Верификация

- `python -m py_compile migrations/versions/004_time_semantic_health.py migrations/versions/005_quota_degrade.py` — PASS.
- `.venv/bin/alembic history` — PASS.
- `.venv/bin/alembic upgrade head --sql` — PASS.
- `.venv/bin/alembic downgrade 005_quota_degrade:004_time_semantic_health --sql` — PASS.

Реальная проверка через PostgreSQL не запускалась: доступность БД в текущем окружении не подтверждена.

## Handoff

Следующий шаг: BACK IMPLEMENT s05-sqlalchemy-models.
