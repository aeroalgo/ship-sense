# [v1-p1-storage | s02 | samples-hypertable] IMPLEMENT

**Plan ID:** v1-p1-storage  
**Decompose step:** [s02-samples-hypertable.md](../../plan/decompose-v1-p1-storage/s02-samples-hypertable.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-29  
**Уровень:** L1 (DDL migration)  
**Статус:** done

## Сделано

- Создана revision `002_samples_hypertable` поверх `001_extensions_timescale`.
- Создана таблица `samples` в схеме `shipsense` через текущий `search_path`.
- Добавлены PK `(tag_id, ts)` и ограничение `quality BETWEEN 0 AND 5`.
- Таблица преобразуется в hypertable по `ts` с chunk interval `1 day` и `if_not_exists => TRUE`.
- Добавлены индексы `idx_samples_tag_ts_desc`, `idx_samples_official_ts`, `idx_samples_edge_ts`.
- Downgrade удаляет chunks перед удалением таблицы.

## Файлы

- `migrations/versions/002_samples_hypertable.py`
- `memory-bank/back/implement/implement-v1-p1-storage/index.md`
- `memory-bank/activeContext.md`

## Верификация

- `.venv/bin/alembic history` — PASS: `001_extensions_timescale -> 002_samples_hypertable (head)`.
- `.venv/bin/alembic upgrade head --sql` — PASS: offline DDL сформирован.
- `.venv/bin/alembic downgrade 001_extensions_timescale:base --sql` — PASS: downgrade DDL сформирован.
- Реальная проверка `\d samples`, `timescaledb_information.hypertables` и upgrade/downgrade на БД не запускалась в этом шаге.
