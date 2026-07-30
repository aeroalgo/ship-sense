# Шаг s10: QuotaManager (disk watch, 80% alert, drop_chunks)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S10 (из плана §224–228, §556–596: alert 80%, degrade samples only, separate quotas, watermark update)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `QuotaManager` — периодический (60s) сбор метрик диска (psutil + pg_total_relation_size), при >=80% — health + log; при превышении samples_quota — drop oldest chunks (только samples), запись в degrade_log, update watermark. Events неприкосновенны.

## Контекст
- **Consumes:** s04 quota_config, s05 schemas, s02 samples hypertable, psutil.
- **Produces:** apps/edge/storage/quota_manager.py.
- **Downstream:** s11 health, writer (call), T-003 (alert UI).
- **План:** §579 (alert), §584 (degrade), §591 (priority), §1103 (health repo later).

## Файлы
- `apps/edge/storage/quota_manager.py` (Создание)
- `tests/storage/test_quota_degrade.py` (Создание)

## Интерфейсы (lean — без кода)
- class QuotaManager:
  - async def check_and_degrade(self) -> DegradeResult: ...
  - async def get_current_usage(self) -> DiskUsage: ...
- DegradeResult: alerted, degraded_chunks, bytes_freed
- Config из storage_quota_config (или env override).

## TDD
- **Да:** mock disk 81% → alert row; mock quota exceed → drop_chunks called, events unchanged.
- Integration: testcontainers + mock pg sizes.
- pytest -k "quota or degrade"

## Подробный процесс выполнения
1. Чтение quota_config (id=1).
2. disk_total = psutil.disk_usage + pg_database_size.
3. При disk_pct >= alert_pct: insert health_snapshots extra.alert="disk_80", WARNING log.
4. samples_bytes > quota: query timescaledb_information.chunks (oldest compressed first), SELECT drop_chunks, insert degrade_log, update watermark.
5. Никогда не трогать events.
6. Приоритет: uncompressed old → compressed old.

## Верификация
- 81% → health row + log.
- Quota exceed → chunks dropped, samples_degrade_log + watermark updated, events count same.
- Блокер: s04, s02.

## Блокеры / CREATIVE
CR-STO-01 (chunk size влияет на degrade granularity).
