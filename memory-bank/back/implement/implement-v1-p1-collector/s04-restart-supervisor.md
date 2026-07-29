# [T-001 | s04 | restart-supervisor] IMPLEMENT

**Plan ID:** v1-p1-collector
**Decompose step:** [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md)
**Creative:** [creative-collector-isolation.md](../../creative/creative-collector-isolation.md) (CR-COL-01)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L4
**AC:** AC-B1-04, AC-B1-05, AC-B1-06, AC-B1-12, AC-HLT-04
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s04-restart-supervisor.md`

## Skills

- tdd, modern-python, python-testing-patterns, property-based-testing (по workflow-implement + creative §2)
- verification-before-completion (перед FINISH)

## Сделано

- Создан `core/restart_policy.py` — `@dataclass(frozen=True) RestartPolicy` (plan §11.4 дословно): `initial_backoff_sec=1.0`, `max_backoff_sec=60.0`, `max_consecutive_failures=None` (infinite), `jitter=True`.
- Создан `util/backoff.py` — `compute_backoff(attempt, policy) → float` (creative §2 вариант 1, **full jitter**):
  - `expo = min(initial * 2**attempt, max)`; без jitter → `expo`; с jitter → `random.uniform(0, expo)`.
  - attempt клампится до 1023, чтобы `2.0**attempt` не переполнял float при гигантских attempt (cap всё равно сработает раньше).
- Создан `core/supervisor.py` — `SourceSupervisor` (creative §1 вариант 1: **supervised asyncio.Task per source**, ADR-COL-002 Accepted):
  - `start()` → `asyncio.create_task(self._run(), name=f"source:{source_id}")` (имя для диагностики `asyncio.all_tasks()`).
  - `_run` → `_supervise` цикл: `connect → subscribe → _wait_until_dead`; на failure — `_consecutive_failures += 1`, backoff sleep, reconnect. `CancelledError` прокидывается (не failure).
  - **Consecutive reset** (creative §2): счётчик сбрасывается в `_on_sample` — первый доставленный сэмпл = подписка реально ожила (не только успешный `connect`).
  - **`max_consecutive_failures`** → состояние `DOWN` (cold): `_is_cold()` прекращает реконнекты, supervisor крутится на `sleep(0.1)` в состоянии DOWN.
  - **State** (AC-B1-06): `RECONNECTING` (init/connect-fail), `UP` (subscribe жива), `DOWN` (cold). DEGRADED — уровень health writer (s14), не хранится в supervisor.
  - **Edge cases** (creative §3): connect OK + subscribe fail → `disconnect()` перед backoff (anti resource leak); `CancelledError` не считается failure; backpressure = `await raw_queue.put` (no drop, данные не теряем).
  - **`stop()`** (AC-HLT-04, creative §3 вариант 1): cancel task → await (`suppress(CancelledError)`) → `disconnect()` **однократно** (guard `_stopped`). Идемпотентен (повторный `stop()` no-op). `stop()` до `start()` всё равно зовёт `disconnect()` (defensive).
- Health-снимок **не дублируется** в supervisor — переиспользуется `BaseSourceConnector.healthcheck()` (s03). Supervisor обновляет только `_state`/`_consecutive_failures` (exposition в Prometheus — s14, **не** s04).

## Файлы

- `apps/edge/collector/src/collector/core/restart_policy.py` (Создание)
- `apps/edge/collector/src/collector/core/supervisor.py` (Создание)
- `apps/edge/collector/src/collector/util/backoff.py` (Создание)
- `apps/edge/collector/tests/unit/test_supervisor.py` (Создание)

## Тесты

- **Runner note:** в проектном `.venv` нет `pytest`/`pytest-asyncio`. Тесты гонятся через `/home/aero/.pyenv/shims/python -m pytest` (pytest 9.1.1, pyenv 3.12.11) + `PYTHONPATH=apps/edge/collector/src`. Async-тесты через `asyncio.run(...)` (как в существующем `test_plugin_registry.py`), **без** `pytest-asyncio`.
- red: `PYTHONPATH=src .venv/../pyenv/python -m pytest tests/unit/test_supervisor.py` → `ModuleNotFoundError: No module named 'collector.core'`.
- cmd targeted: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/unit/test_supervisor.py`
- итог targeted: `16 passed in 0.34s`.
- cmd regression: `PYTHONPATH=src /home/aero/.pyenv/shims/python -m pytest -q tests/`
- итог regression: `40 passed in 0.37s` (s01/s02/s03 чисто).

Покрытие targeted (чекпоинты creative §5):
- backoff jitter-off `[1,2,4,8,16,32,60,60,...]` (AC-B1-05 монотонность/cap).
- backoff cap 60 при `attempt=100/1000/100000` (overflow-safe).
- backoff jitter-on range `[0, min(initial*2**attempt, max)]` × 200.
- backoff jitter-off детерминизм.
- `RestartPolicy` defaults (1.0 / 60.0 / None / True).
- supervisor форвардит RawSample → `raw_queue` (AC-B1-12 путь данных).
- `stop()` cancel + disconnect ровно 1 раз + task done (AC-HLT-04).
- `stop()` идемпотентен (двойной вызов → 1 disconnect).
- `stop()` до `start()` → disconnect вызван (defensive).
- **dual-source isolation (AC-B1-04):** fake A бесконечно падает в subscribe, fake B продолжает `put` в общую queue — сэмплы с `source_id == skt_geu` доходят.
- consecutive reset на first sample (connect_fails=2 → recovery → push → counter 0).
- reconnect с backoff recovery (connect_fails=3 → `connect_calls == 4`, alive).
- **max_consecutive_failures=3 → DOWN** (cold, `connect_calls == 3`).
- subscribe failure → disconnect перед backoff.
- shutdown (cancel) не накручивает consecutive failures.
- **subscribe-fail изоляция (AC-B1-04):** A падает в subscribe, B жив, disconnect A≥1, B==1.

Примечание по тестовой стратегии: малый backoff в policy (`initial_backoff_sec=0.001`) вместо реальных `asyncio.sleep(1..60)` — тесты быстрые, проверяют **значения** delay через pure-функцию + состояние счётчика (creative §5 «без реальных asyncio.sleep»). В dual-isolation оба супервизора на общей `asyncio.Queue` (AC-B1-04 «отдельные put paths» = разные task-продюсеры, одна очередь).

## Integration check (§0.11)

- [x] N/A — слой in-process lifecycle: нет storage keys / env vars / DB cols / IPC routes (counterpart для wire появится в s05 queues + s05b IPC). `connect_fails`/`subscribe_fails` покрыты fake-коннектором.
- [x] `SourceConnector`, `Subscription`, `RawSample`, `SourceState`, `ConnectError` — переиспользованы из s01/s03 (новых доменных контрактов нет).
- [x] `BaseSourceConnector.healthcheck()` из s03 — переиспользован, **не** дублирован в supervisor (creative §6).
