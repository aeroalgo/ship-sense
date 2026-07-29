# Шаг s05: In-proc raw/canonical queues + raw_consumer bridge
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-INT-01, AC-HLT-03, ADR-COL-001

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
In-proc raw/canonical queues + raw_consumer bridge — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01 models; s03 CanonicalSink protocol
- **Produces:** raw/canonical/event queues; raw_consumer; queue_sink/null/mock sinks

## Файлы
- `apps/edge/collector/src/collector/core/raw_consumer.py` (Создание)
- `apps/edge/collector/src/collector/sink/__init__.py` (Создание)
- `apps/edge/collector/src/collector/sink/queue_sink.py` (Создание)
- `apps/edge/collector/src/collector/sink/null_sink.py` (Создание)
- `apps/edge/collector/src/collector/sink/mock_sink.py` (Создание)
- `apps/edge/collector/tests/unit/test_queues_pipeline.py` (Создание)

## Интерфейсы (lean — без кода)
- queues: `asyncio.Queue[RawSample]`, `Queue[TelemetrySample]`, `Queue[Event]` — только внутри collector
- class: `RawConsumer` — drain raw → callback/normalizer hook
- class: `QueueSink(CanonicalSink)` — put sample/event в canonical queues
- class: `MockSink` — counters для тестов
- class: `NullSink` — drop

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_queues_pipeline.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Собрать in-proc pipeline без IPC: raw → consumer → (passthrough stub) → sink.
2. MockSink считает samples; нет потери при burst put/get.
3. Запрет: не шарить queue с api-процессом.

## Чекпоинт верификации
- MockSink.count == N после N put
- queue_depth counters доступны
- нет Redis/Kafka в зависимостях шага
