# [T-001 | s05b | ipc-to-writer] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s05b-ipc-to-writer.md](../../plan/decompose-v1-p1-collector/s05b-ipc-to-writer.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2
**AC:** AC-INT-01, AC-INT-02, стык T-002 §21.1
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s05b-ipc-to-writer.md`

## Skills
- tdd, modern-python, python-testing-patterns (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `sink/ipc_sink.py` — `IpcCanonicalSink` (CanonicalSink contract):
  - `__init__(endpoint, *, connect_attempts=5, retry_delay=0.2)`.
  - `endpoint: str | PathLike` → **Unix socket** (файл);
    `endpoint: (host, port)` → **localhost TCP**. Транспорт выбирается по типу.
  - `connect()` → bounded reconnect (`_connect_with_retries`, `connect_attempts`,
    backoff `retry_delay`). При истечении → **`SinkUnavailable`**.
  - `write_sample(sample)` / `write_event(event)` → framing + send
    (`_send` под `_lock`, reconnect-on-обрыв + ровно один retry).
  - `flush()` → `writer.drain()` (await отправки буфера транспорта).
  - `close()` → idempotent (`_close_unchecked` сбрасывает reader/writer, suppress ошибок).
  - `_drop_connection()` — test hook для имитации обрыва без reconnect.
  - **Framing:** 4-byte big-endian length + UTF-8 JSON envelope
    `{"type":"sample"|"event","payload":{...}}`. Binary-safe
    (без delimiter-ambiguity NDJSON). Сериализация payload —
    `model.model_dump(mode="json")` (datetime → ISO, enum → value).
  - **Политика потери связи:** явная `SinkUnavailable`, не silent drop
    (§21.1 / ADR-COL-001 collector обязан сигнализировать потерю стыка).
    `CancelledError` всегда прокидывается (graceful stop).
- Создан `sink/__init__.py` (Модификация) — реэкспорт добавлен:
  `IpcCanonicalSink`, `SinkUnavailable` (вместе с `MockSink`/`NullSink`/`QueueSink`).
- Создан `README.md` — framing wire-контракт + таблица транспорта + политика
  потери связи + указание peer'а (compose service `writer`, T-002).

## Файлы
- `apps/edge/collector/src/collector/sink/ipc_sink.py` (Создание)
- `apps/edge/collector/src/collector/sink/__init__.py` (Модификация)
- `apps/edge/collector/tests/unit/test_ipc_sink.py` (Создание)
- `apps/edge/collector/README.md` (Создание)

## Тесты
- **Runner note:** тесты гонятся через `/home/aero/.pyenv/shims/python -m pytest`
  (pytest 9.1.1, pyenv 3.12.11) + `PYTHONPATH=apps/edge/collector/src`.
  Async-тесты через `asyncio.run(scenario())` (как в `test_supervisor.py` /
  `test_queues_pipeline.py`), **без** `pytest-asyncio`.
  Mock writer — `asyncio.start_server` (TCP) / `asyncio.start_unix_server`
  (Unix), читает length-prefixed frames.
- red: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_ipc_sink.py`
  → `ModuleNotFoundError: No module named 'collector.sink.ipc_sink'`.
- cmd targeted: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/unit/test_ipc_sink.py`
- итог targeted: `7 passed in 0.11s`.
- cmd regression: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/`
- итог regression: `56 passed in 0.44s` (s01–s05b чисто; +7 к s01–s05=49).

Покрытие (чекпоинты decompose §«Чекпоинт верификации»):
- round-trip `TelemetrySample` + `Event` через mock writer (TCP):
  payload бит-в-бит (`tag_id`, `quality=="good"`, `value`, `idempotency_key` non-empty).
- Несколько frames в одном соединении — framing без delimiter ambiguity (5 samples, values 0–4).
- Reconnect после обрыва транспорта (`_drop_connection`): следующий write проходит (values [1, 2]).
- Сервер отсутствует, попытки истекли → `SinkUnavailable` (connect + write) — не silent drop.
- Unix socket transport — тот же envelope, файловый путь вместо host:port.
- `IpcCanonicalSink` структурно соответствует `CanonicalSink` (callable `write_sample`/`write_event`).
- `close()` idempotent (двойной close без исключения).
- README описывает framing; compose service `writer` упомянут как peer.

## §0.11 Integration
- Новых routes/keys/env/cols/migrations — нет. Шаг = IPC client класс + README
  (framing контракт для server-side T-002 writer).
- Broker grep: `redis|kafka|aiormq|pika|nats` в `sink/` — **none**
  (подтверждено: только `asyncio.open_connection`/`open_unix_connection`).
- Peer стыка (writer server stub, `canonical_queue`, compose `writer`) —
  server-side T-002, **не** входит в T-001 (план §6.8: sink = IPC client,
  server = T-002). Контракт зафиксирован в README.
