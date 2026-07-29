# Шаг s16: Compression + retention policy (Alembic 006, after CREATIVE)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK CREATIVE
**needs_creative:** yes (CR-STO-01/02) | **tdd:** no
**AC:** AC-STO-S16 (из плана §527–538, §973: compress after 7d, segmentby tag_id, orderby ts DESC; retention 1095d soft; add_compression_policy)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать миграцию 006: ALTER TABLE samples SET (timescaledb.compress ...); SELECT add_compression_policy('samples', INTERVAL '7 days'); add_retention_policy 1095 days. Выполняется **после** закрытия CREATIVE CR-STO-01/02.

## Контекст
- **Consumes:** s02 samples hypertable; CREATIVE ADR + benchmark (chunk/compress).
- **Produces:** `migrations/versions/006_compression_retention.py`
- **Downstream:** production disk savings; T-007 watermark guard.
- **План:** §528 (DDL policies), §981 (rec 7d), §539 (retention soft).

## Файлы
- `migrations/versions/006_compression_retention.py` (Создание)

## Интерфейсы (lean — без кода)
- ALTER + add_compression_policy + add_retention_policy.
- downgrade: remove policies (SELECT remove_compression_policy etc.) before drop.

## TDD
- Нет (DDL + policy).
- Верификация: после upgrade policies видны в timescaledb_information.compression_settings; chunks compressable.

## Подробный процесс выполнения
1. Ждать CREATIVE (benchmark chunk 1d vs 7d, compress ratio ≥5×).
2. DDL точно из плана §529–537.
3. Комментарий: после CR-STO-01/02; retention soft (quota degrade может раньше).
4. Downgrade: remove policies + ALTER no compress.

## Верификация
- `SELECT * FROM timescaledb_information.compression_settings;`
- `SELECT add_compression_policy...` идемпотентно при rerun.
- Блокер: CREATIVE closed + s02.

## Блокеры / CREATIVE
**Обязательно** CR-STO-01 chunk, CR-STO-02 compress params перед этим шагом.
