# Шаг s14: HealthAggregator + JSON snapshot writer + metrics
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B1-07, AC-B1-12, AC-HLT-01, AC-HLT-02, AC-HLT-03, AC-HLT-05

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
HealthAggregator + JSON snapshot writer + metrics — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01 CollectorHealthSnapshot; s04 supervisor health
- **Produces:** health aggregator, snapshot file writer, structured logging hooks, app wiring start

## Файлы
- `apps/edge/collector/src/collector/health/aggregator.py` (Создание)
- `apps/edge/collector/src/collector/health/snapshot_writer.py` (Создание)
- `apps/edge/collector/src/collector/health/metrics.py` (Создание)
- `apps/edge/collector/src/collector/app.py` (Создание) — CollectorApp skeleton wire
- `apps/edge/collector/src/collector/__main__.py` (Создание)
- `apps/edge/collector/tests/unit/test_health_snapshot.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `HealthAggregator` — update_source, bump counters, snapshot()
- class: `SnapshotWriter` — write JSON every N sec (default 5)
- class: `CollectorApp` — start/stop sources, normalizer, health, SIGTERM→0

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_health_snapshot.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Агрегат per-source + global; file snapshot для T-003.
2. structlog fields: source_id, event, latency, error_code.
3. Graceful SIGTERM: drain + disconnect → exit 0.

## Чекпоинт верификации
- snapshot JSON обновляется
- counters samples_in/out/errors/queue_depth
- stop clean
