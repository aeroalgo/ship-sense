# Шаг s04: meta, health, clock_shift, quota tables (Alembic 004 + 005)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S04 (из плана §438–522: clock_shift_log, semantic_meta, tag_quarantine, health_snapshots, storage_quota_config, samples_degrade_log, watermark stub)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать вспомогательные таблицы для B7/B8/health/quota: semantic_meta, tag_quarantine, clock_shift_log, health_snapshots, storage_quota_config (seed 8TiB), samples_degrade_log, samples_degrade_watermark (stub для B9).

## Контекст
- **Consumes:** s01; план §438–550 (DDL).
- **Produces:** миграции 004 и 005; foundation для SemanticEngine (s13), QuotaManager (s10), Health (s11), TimeAxis (s08).
- **Downstream:** s08, s10, s11, s13, s15.

## Файлы
- `migrations/versions/004_time_semantic_health.py` (Создание — clock, semantic, health, quarantine)
- `migrations/versions/005_quota_degrade.py` (Создание — quota_config, degrade_log, watermark)

## Интерфейсы (lean — без кода)
- semantic_meta: pack_name, version, approved_at, checksum, manifest JSONB, UNIQUE(pack,version).
- tag_quarantine: tag_id PK, reason, since, native_id_hint, acknowledged.
- clock_shift_log: detected_at, detected_on (edge|source), delta, prev_ts, new_ts, linked_event_id.
- health_snapshots: captured_at, disk_*, ram_*, cpu_*, samples_bytes, events_bytes, extra JSONB.
- storage_quota_config: id=1, disk_total_bytes=8TiB, alert_pct=80, samples_quota_pct=85, events=10, headroom=5.
- samples_degrade_log: degraded_at, chunk_start/end, reason, rows_estimate.
- samples_degrade_watermark: oldest_sample_ts (stub).

## TDD
- DDL; psql verify + seed insert.
- alembic up/down.

## Подробный процесс выполнения
1. DDL из плана §440–550 точно.
2. INSERT в quota_config ON CONFLICT DO NOTHING.
3. Комментарии с ссылками на план (CR-STO-03 для quarantine).
4. Downgrade: DROP TABLE.

## Верификация
- Таблицы существуют; индексы на since/desc.
- Seed quota_config: 8589934592000 bytes.
- Watermark stub не влияет на s01–s15.
- Блокер: s01.

## Блокеры / CREATIVE
CR-STO-03 (quarantine UX) — флаги в tag_quarantine + quality позже.
