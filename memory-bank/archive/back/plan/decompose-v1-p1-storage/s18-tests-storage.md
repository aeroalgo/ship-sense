# Шаг s18: Tests storage (unit + integration + load 586/s)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S18 (из плана §913–955: unit per module, integration e2e + correlation + degrade, load test 586/s p95 + linear growth)
**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python.SKILL.md`

## Цель
Покрыть весь storage слой targeted тестами: unit для time_axis/samples_repo/events_repo/semantic/quota/health; integration (testcontainers) e2e writer, correlation, degrade; load harness 586/s (CI 120s / nightly 1h) с asserts zero drops, p95 flush, R² growth.

## Контекст
- **Consumes:** все s01–s17 (repos, writer, engine, quota и т.д.).
- **Produces:** `tests/storage/` (unit + integration + fixtures); load test `test_load_586hz.py`.
- **Downstream:** CI, soak T1, BACK QA.
- **План:** §915 (unit table), §928 (integration), §934 (load), §952 (fixtures), §145 (pytest-asyncio; parent only runs full).

## Файлы
- `tests/storage/test_time_axis.py` (Создание)
- `tests/storage/test_samples_repo.py` (Создание)
- `tests/storage/test_events_repo.py` (Создание)
- `tests/storage/test_writer_batch.py` (Создание)
- `tests/storage/test_quota_degrade.py` (Создание)
- `tests/storage/test_health_snapshot.py` (Создание)
- `tests/storage/test_semantic_loader.py` (Создание)
- `tests/storage/test_semantic_engine.py` (Создание)
- `tests/storage/test_quarantine.py` (Создание)
- `tests/storage/test_load_586hz.py` (Создание)
- `tests/fixtures/ship-pack-minimal/` (Создание — 5 tags)
- `tests/fixtures/events_q4a.jsonl`, `events_q4b.jsonl` (Создание)
- `tests/conftest.py` (Update — timescale container fixture)

## Интерфейсы (lean — без кода)
- Unit: parametrize official_ts cases, dedup quality, idempotency, diff → quarantine list, mock disk → alert.
- Integration: push 1000 samples+10 events → count match; event + samples → get_with_sample; fill quota → drop_chunks, events unchanged.
- Load: producer task 586/s + 2 events/s; assert zero queue drops (в writer), p95 flush <100ms, disk growth linear R²>0.95 (1h).

## TDD
- **Да:** все тесты TDD-style (многие red-green в процессе).
- Targeted: pytest tests/storage/ -k "unit or integration" (не load в CI по умолчанию).
- Load: отдельно, parent запускает (subagent не).

## Подробный процесс выполнения
1. Создать fixtures: minimal pack (5 tags), Q4A/B event lines.
2. Conftest: async engine + testcontainers postgres+timescale (pin 2.14.2-pg16).
3. Unit per module как в плане §915–927.
4. Integration 3 теста из §930–932.
5. Load harness: asyncio producer mimicking T-001 canonical, writer.run в фоне, stats collection, asserts.
6. Добавить маркеры: @pytest.mark.integration, @pytest.mark.load.
7. В pyproject.toml / pytest.ini — markers + timeout для load.

## Верификация
- Все unit/integration pass targeted.
- Load 120s CI: exit 0, metrics in log.
- Nightly 1h: linear growth.
- Блокер: s09 (writer), s06–s08, s10–s15.

## Блокеры / CREATIVE
Нет. Load metrics зависят от реального writer throughput (s09).

**Примечание:** subagent создаёт тесты; запуск compose / full load / pytest suite — только parent (как в mqtt-smoke).
