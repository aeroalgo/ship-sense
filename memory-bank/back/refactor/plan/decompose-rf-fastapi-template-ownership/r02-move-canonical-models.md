# Шаг r02: Move Quality/TelemetrySample/Event* → `app.*`
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** yes  
**Priority:** Critical  
**Depends:** r01  
**code_changed:** yes  
**AC:** plan §5.2 AC B

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

---

## Цель
Канон `Quality`, `TelemetrySample`, `Event`, `EventSeverity` живёт только в `app.telemetry.models` / `app.events.models`. Collector domain = Raw* + health. Storage/collector/tests переведены на `app.*`. Один atomic move — **без** долгого dual-source shim.

## Контекст
- **Consumes:** r01 (`apps/api` + pythonpath); freeze snapshot plan §7.4; import map §7.1–7.3; Shared Kernel §3.1.
- **Produces:** канон под `app.*`; `raw_models.py` + `health_models.py`; нулевые импорты storage→collector.domain canonical.

## Файлы
- `apps/api/app/telemetry/models.py` (Создание) — Quality, TelemetrySample
- `apps/api/app/events/models.py` (Создание) — EventSeverity, Event
- `apps/edge/collector/src/collector/domain/raw_models.py` (Создание) — RawSample, RawTagDescriptor
- `apps/edge/collector/src/collector/domain/health_models.py` (Создание) — SourceState, HealthStatus, CollectorHealthSnapshot
- `apps/edge/collector/src/collector/domain/models.py` (Удаление или опустошение→удаление) — канон убрать
- `apps/edge/collector/src/collector/domain/__init__.py` (Модификация) — `__all__` без TelemetrySample/Event/Quality
- `apps/edge/collector/src/collector/domain/interfaces.py` (Модификация) — CanonicalSink → app.* types
- `apps/edge/collector/src/collector/core/normalizer.py` (Модификация)
- `apps/edge/collector/src/collector/core/raw_consumer.py` (Модификация)
- `apps/edge/collector/src/collector/core/quality_engine.py` (Модификация)
- `apps/edge/collector/src/collector/core/event_detector.py` (Модификация)
- `apps/edge/collector/src/collector/sink/*_sink.py` (Модификация)
- `apps/edge/collector/src/collector/app.py` (Модификация)
- `apps/edge/collector/src/collector/plugins/mqtt/lifecycle_tracker.py` (Модификация) — Event из app.events
- `apps/edge/collector/src/collector/plugins/mqtt/mapper.py` (Модификация) — Event из app.events
- `apps/edge/storage/writer.py` (Модификация)
- `apps/edge/storage/samples_repo.py` (Модификация)
- `apps/edge/storage/events_repo.py` (Модификация)
- `tests/storage/test_*.py`, `tests/pipeline/**`, `apps/edge/collector/tests/**` (Модификация) — импорты
- Docker/compose PYTHONPATH / Dockerfile COPY (Модификация при необходимости) — runtime видит `apps/api`

**Plugins connectors (modbus/opcua/mqtt transport):** не тянуть `app.telemetry`/`app.events` — только Raw*.

## Интерфейсы (lean — без кода)
- enum: `Quality` — good|bad|uncertain|stale|quarantine (значения freeze)
- model: `TelemetrySample` — tag_id, value, unit, source_ts, edge_ts, quality, source_id, native_id?
- enum: `EventSeverity` — info|warning|alarm|protection
- model: `Event` — event_name, params, ts, edge_ts, source, tag_id?, severity, idempotency_key, quality
- model: `RawSample`, `RawTagDescriptor` — как as-is в collector
- model: `SourceState`, `HealthStatus`, `CollectorHealthSnapshot` — как as-is
- rule: `app.telemetry.models` / `app.events.models` **не** импортируют fastapi/starlette/`app.api`/`app.main`
- rule: запрещён shim >1 rNN (два источника правды)

## TDD (красная → зелёная)
1. **Before:** `.venv/bin/pytest apps/edge/collector/tests tests/storage tests/pipeline -q --tb=line` green (baseline; `addopts` уже `-m 'not slow'` — soak/pipeline slow не в default).
2. **Тесты:** существующие IPC/writer/normalizer — ожидают те же wire keys; обновить только import paths.
3. **Refactor:** move + rewire одним проходом.
4. **After:** тот же scope green; `rg` checks AC B. Slow/soak отдельно: `.venv/bin/pytest … -m slow --override-ini="addopts="`.

## Подробный процесс выполнения
1. Скопировать байт-в-байт поля/defaults канона в `app.telemetry.models` / `app.events.models`.
2. Split Raw*/health в collector domain; удалить канон из `models.py`.
3. Переписать импорты storage → `app.*`; collector core/sinks/interfaces → `app.*` + Raw* local.
4. MQTT lifecycle/mapper — `app.events` (application-side OK).
5. Проверить PYTHONPATH в compose/Docker для collector/writer.
6. Не менять `model_dump` aliases / IPC JSON.

## Чекпоинт верификации
- Определения TelemetrySample/Quality/Event* только под `app.*`
- `rg "collector.domain.models import.*Quality"` в storage/tests = 0
- IPC roundtrip / writer batch tests green
- `app.*.models` без fastapi imports
- `.venv/bin/graphify update .` на FINISH
