# Шаг s13: B4 Normalizer: raw → TelemetrySample + Event detector
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B4-01, AC-B4-02, AC-B4-05, AC-B4-06, AC-B4-10, AC-B4-11, AC-B4-13

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
B4 Normalizer: raw → TelemetrySample + Event detector — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s05 queues; s11; s12; tag maps s02
- **Produces:** normalizer + event_detector + util/time; worker loop

## Файлы
- `apps/edge/collector/src/collector/core/normalizer.py` (Создание)
- `apps/edge/collector/src/collector/core/event_detector.py` (Создание)
- `apps/edge/collector/src/collector/util/time.py` (Создание)
- `apps/edge/collector/tests/unit/test_normalizer.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `Normalizer` — process(RawSample) → TelemetrySample | None; side Event?
- class: `EventDetector` — discrete change → Event (Q4 stub)
- fn: `utc_now() → datetime` aware
- dedup: same native_id+source_ts → one canonical

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_normalizer.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Map native_id→tag_id; unit convert; quality; edge_ts всегда; source_ts fallback = edge_ts.
2. Idempotent dedup; discrete → Event.
3. Грязь не роняет worker (exceptions → bad sample / log).

## Чекпоинт верификации
- Modbus↔OPC same tag_id structure
- duplicate → one sample
- worker не падает на NaN
