# Шаг s02: samples hypertable (Alembic 002)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S02 (из плана §185–193 B5: hypertable, PK, indexes, chunk 1d)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать таблицу `samples` как hypertable TimescaleDB: PK (tag_id, ts), поля ts/source_ts/edge_ts/official_ts/value/quality, базовые индексы, chunk_time_interval = 1 day. Без compression/retention (это s16 после CREATIVE).

## Контекст
- **Consumes:** s01 (search_path shipsense); план §342–372 (DDL + обоснование chunk).
- **Produces:** миграция 002; основа для SamplesRepo (s06).
- **Upstream:** T-001 TelemetrySample (tag_id, value, quality, *_ts).
- **Downstream:** s06, s10 (degrade), writer.

## Файлы
- `migrations/versions/002_samples_hypertable.py` (Создание)

## Интерфейсы (lean — без кода)
- `CREATE TABLE samples (...)` с CONSTRAINT quality 0-5, PK (tag_id, ts).
- `SELECT create_hypertable('samples', 'ts', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);`
- Индексы: idx_samples_tag_ts_desc, idx_samples_official_ts, idx_samples_edge_ts.

## TDD
- **Причина:** DDL; проверка через psql + Timescale helpers.
- **Верификация (parent):**
  1. alembic upgrade +1 (после s01).
  2. `\d samples` — hypertable, chunk 1d.
  3. `SELECT * FROM timescaledb_information.hypertables WHERE table_name='samples';`
  4. downgrade + upgrade без потери данных (тест на пустой БД).

## Подробный процесс выполнения
1. Взять DDL точно из плана §344–367.
2. Добавить комментарий: chunk 1 day по CR-STO-01 (benchmark позже).
3. Оценка строк: 586*86400 ≈ 50.6M /day.
4. В downgrade: `SELECT drop_chunks(...)` + `DROP TABLE`.

## Верификация
- `SELECT create_hypertable` идемпотентен (if_not_exists).
- Индексы на (tag_id, ts DESC) — для трендов.
- Нет данных — только структура.
- Блокер: timescale extension (s01).

## Блокеры / CREATIVE
Нет (chunk default принят в плане; CR-STO-01 — ADR после benchmark).
