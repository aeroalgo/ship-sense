# Шаг s06: SamplesRepo (batch insert, dedup, trend query)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S06 (из плана §186–194, §1101: insert_batch с COPY/executemany + dedup quality, query_trend, query_point)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `SamplesRepo` — async методы для батчевой записи samples (с dedup по quality last-wins / better-wins), query_trend (tag_id, t0, t1, max_points), query_point. Использует SQLA + asyncpg / COPY.

## Контекст
- **Consumes:** s05 schemas.Sample; T-001 TelemetrySample (tag_id, value, unit?, source_ts, edge_ts, official_ts, quality).
- **Produces:** apps/edge/storage/samples_repo.py; injectable в writer.
- **Downstream:** s09 writer, T-003 (read-only).
- **План ссылки:** §344 (DDL), §597 (dedup policy ON CONFLICT), §1101 (interface), §186 (throughput).

## Файлы
- `apps/edge/storage/samples_repo.py` (Создание)
- `apps/edge/storage/__init__.py` (Update — expose)
- `tests/storage/test_samples_repo.py` (Создание — unit + integration с testcontainers)

## Интерфейсы (lean — без кода)
- class SamplesRepo:
  - async def insert_batch(self, samples: list[TelemetrySample]) -> int: ...  # возвращает inserted (после dedup)
  - async def query_trend(self, tag_id: str, t0: datetime, t1: datetime, max_points: int = 1000) -> list[SamplePoint]: ...
  - async def query_point(self, tag_id: str, ts: datetime) -> SamplePoint | None: ...
- SamplePoint: dataclass tag_id, ts, value, quality, official_ts ...
- Dedup: ON CONFLICT (tag_id, ts) DO UPDATE quality лучше wins (lower code), last on equal.

## TDD
- **Да:** red (тест на insert + duplicate worse/better quality) → green (repo) → refactor.
- Тесты: mock engine, real testcontainers postgres+timescale.
- Targeted: pytest tests/storage/test_samples_repo.py -k "dedup or trend"
- Load фрагмент позже в s18.

## Подробный процесс выполнения
1. Определить async session / engine factory (из конфига).
2. insert_batch: если len >= copy_threshold → COPY (asyncpg), else executemany + ON CONFLICT.
3. Реализовать exact dedup SQL из плана §600–612.
4. query_trend: bucket/ resample? (пока raw limit max_points; later downsample в T-003).
5. query_point: точный (tag_id, ts) или closest.
6. Метрики: writer_samples_total, dedup_total.
7. Graceful: commit в транзакции.

## Верификация
- 1000 samples + 500 duplicate worse quality → row count 1000, final quality = better.
- query_trend 24h p95 <500ms (dev, на 86k точек).
- query_point p95 <50ms.
- Блокер: s05 (models), s02 (table).

## Блокеры / CREATIVE
Нет.
