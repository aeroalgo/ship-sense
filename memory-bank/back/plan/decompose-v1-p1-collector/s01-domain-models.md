# Шаг s01: Domain models (Quality, RawSample, TelemetrySample, Event, Health)
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B4-01 (поля канона), AC-B4-04 (enum Quality), AC-B1-06 (SourceState), AC-HLT-02 (CollectorHealthSnapshot shape)

**code_surface:** model

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Domain models (Quality, RawSample, TelemetrySample, Event, Health) — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** план §7 контракты; systemPatterns quality enum
- **Produces:** collector.domain.models + errors; shared типы для всех последующих шагов

## Файлы
- `apps/edge/collector/src/collector/domain/__init__.py` (Создание)
- `apps/edge/collector/src/collector/domain/models.py` (Создание) — Quality, RawSample, RawTagDescriptor, TelemetrySample, Event, EventSeverity, HealthStatus, SourceState, CollectorHealthSnapshot
- `apps/edge/collector/src/collector/domain/errors.py` (Создание) — ConnectError, ConfigError
- `apps/edge/collector/tests/unit/test_domain_models.py` (Создание)

## Интерфейсы (lean — без кода)
- enum: `Quality` — good|bad|uncertain|stale|quarantine
- enum: `SourceState` — up|reconnecting|down|degraded
- enum: `EventSeverity` — info|warning|alarm|protection
- model: `RawSample` — source_id, native_id, raw_value, native_quality?, recv_ts, source_ts?, sequence?
- model: `RawTagDescriptor` — native_id, name?, unit?, datatype?, description?
- model: `TelemetrySample` — tag_id, value, unit, source_ts, edge_ts, quality, source_id, native_id?
- model: `Event` — event_name, params, ts, edge_ts, source, tag_id?, severity, idempotency_key, quality
- model: `HealthStatus` — source_id, state, last_ok_ts?, reconnect_count, detail?, tags_total, tags_active, sample_rate_hz?
- model: `CollectorHealthSnapshot` — ts, collector_state, sources, queue_raw_depth, queue_canonical_depth, samples_total, events_total, errors_total

## TDD (красная → зелёная)
1. **Тест:** `apps/edge/collector/tests/unit/test_domain_models.py` — валидация/сериализация моделей §7
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Создать пакет domain и Pydantic-модели строго по plan §7 (имена полей без расхождений).
2. Добавить unit-тесты: сериализация round-trip, enum values, обязательные поля.
3. Не добавлять бизнес-логику нормализации — только контракты данных.

## Чекпоинт верификации
- Все модели импортируются из `collector.domain.models`
- pytest unit/test_domain_models.py green
- Quality содержит ровно 5 значений
