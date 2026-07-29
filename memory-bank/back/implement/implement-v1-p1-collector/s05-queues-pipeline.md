# [T-001 | s05 | queues-pipeline] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s05-queues-pipeline.md](../../plan/decompose-v1-p1-collector/s05-queues-pipeline.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2
**AC:** AC-INT-01, AC-HLT-03, ADR-COL-001
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s05-queues-pipeline.md`

## Skills
- tdd, modern-python, python-testing-patterns (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `sink/queue_sink.py` — `QueueSink` (CanonicalSink contract):
  - `__init__(canonical: asyncio.Queue[TelemetrySample], events: asyncio.Queue[Event])`.
  - `write_sample` → `canonical.put`; `write_event` → `events.put`.
  - `sample_depth` / `event_depth` (через `qsize`) — для health snapshot без деструктивного get.
  - In-proc only: очереди живут в collector process, **не шарятся с api-процессом** (ADR-COL-001).
- Создан `sink/null_sink.py` — `NullSink`: pure drop, без счётчиков (dev/test заглушка, CanonicalSink contract).
- Создан `sink/mock_sink.py` — `MockSink`: счётчики `samples`/`events`, `last_sample`/`last_event` (тесты).
- Создан `sink/__init__.py` — реэкспорт `QueueSink`, `NullSink`, `MockSink`.
- Создан `core/raw_consumer.py` — `RawConsumer` (drain raw → normalizer → sink):
  - `__init__(raw_queue, sink: CanonicalSink, normalize: Callable[[RawSample], Awaitable[TelemetrySample]])`.
  - `raw_depth` — `raw_queue.qsize()` (health).
  - `start()` → фоновый `_loop` (asyncio.Task `name="raw_consumer:drain"`): `get → normalize → sink.write_sample`. Cancel-friendly (`CancelledError` прокидывается).
  - `drain_once(batch)` — синхронный слив до `batch` samples (через `get_nowait`), возвращает число обработанных; для тестов burst без потери.
  - `stop()` — cancel task → await (`suppress(CancelledError)`) → None; идемпотентен.
  - **Passthrough normalizer** — hook для будущей канонизации (s11 quality, s13 normalizer); сейчас плагин передаётся извне, шаг s05 не реализует саму нормализацию (YAGNI — только bridge).
  - **Запрет:** никакого Redis/Kafka/broker — только `asyncio.Queue` (AC-HLT-03, чекпоинт «нет Redis/Kafka в зависимостях шага»).

## Файлы
- `apps/edge/collector/src/collector/core/raw_consumer.py` (Создание)
- `apps/edge/collector/src/collector/sink/__init__.py` (Создание)
- `apps/edge/collector/src/collector/sink/queue_sink.py` (Создание)
- `apps/edge/collector/src/collector/sink/null_sink.py` (Создание)
- `apps/edge/collector/src/collector/sink/mock_sink.py` (Создание)
- `apps/edge/collector/tests/unit/test_queues_pipeline.py` (Создание)

## Тесты
- **Runner note:** тесты гонятся через `/home/aero/.pyenv/shims/python -m pytest` (pytest 9.1.1, pyenv 3.12.11) + `PYTHONPATH=apps/edge/collector/src`. Async-тесты через `asyncio.run(scenario())` (как в существующих `test_supervisor.py`/`test_plugin_registry.py`), **без** `pytest-asyncio`.
- red: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_queues_pipeline.py` → `ModuleNotFoundError: No module named 'collector.core.raw_consumer'`.
- cmd targeted: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/unit/test_queues_pipeline.py`
- итог targeted: `9 passed in 0.11s`.
- cmd regression: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/`
- итог regression: `49 passed in 0.37s` (s01–s05 чисто).

Покрытие (чекпоинты decompose §«Чекпоинт верификации»):
- MockSink.count == N после N write (samples + events; last_sample/last_event).
- NullSink drop без исключения.
- QueueSink put sample/event в правильные очереди; `qsize` растёт.
- QueueSink `sample_depth`/`event_depth` доступны без get (health snapshot).
- QueueSink структурно соответствует CanonicalSink (write_sample/write_event callable).
- RawConsumer drain raw → passthrough normalizer → sink: burst N=50 без потери (`sample_depth == 50`).
- RawConsumer пустая raw_queue → drained == 0, sink пуст, exit без исключения.
- RawConsumer `raw_depth` без get (health).
- In-proc only: raw/canonical/event — все `asyncio.Queue`, нет broker client (запрет ADR-COL-001).

## §0.11 Integration
- Новых routes/keys/env/cols/migrations — нет. Шаг pure in-proc (asyncio.Queue), без counterparts в api-процессе. Нечего grep-ить (чекпоинт decompose: «нет Redis/Kafka в зависимостях шага» — подтверждено, broker-импортов нет).
