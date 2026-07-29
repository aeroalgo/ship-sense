# [T-001 | s14 | health-snapshot] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s14-health-snapshot.md](../../plan/decompose-v1-p1-collector/s14-health-snapshot.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2
**AC:** AC-B1-07, AC-B1-12, AC-HLT-01, AC-HLT-02, AC-HLT-03, AC-HLT-05
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s14-health-snapshot.md`

## Skills
- tdd, python-testing-patterns, modern-python, python-anti-patterns (по decompose step)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `health/metrics.py` — `Metrics` (AC-HLT-03):
  - `samples_in`/`samples_out`/`errors` — bump_* методы.
  - `queue_raw_depth`/`queue_canonical_depth` — set_queue_depths (внешние, от RawConsumer/QueueSink).
  - Per-source метрики (uptime, reconnects, last_ok_ts, sample_rate) — в `HealthStatus` (domain/models.py), не здесь.
- Создан `health/aggregator.py` — `HealthAggregator` (AC-B1-07, AC-B1-12):
  - `update_source(status)` — перезаписывает статус по source_id.
  - `bump_*` / `set_queue_depths` — делегируют в Metrics.
  - `snapshot(collector_state)` → `CollectorHealthSnapshot` (UTC ts, sources list, counters).
  - `stop()` — безопасный no-op (идемпотентен).
- Создан `health/snapshot_writer.py` — `SnapshotWriter` (AC-HLT-02):
  - `__init__(path, interval_sec=5)`.
  - `write(snapshot)` — сериализует JSON, создаёт parent dir.
  - Stateless (write вызывается снаружи; writer loop — позже).
- Создан `health/__init__.py` — реэкспорт.
- Создан `app.py` — `CollectorApp` skeleton (AC-HLT-04, AC-HLT-05 prep):
  - `__init__(raw_queue, sink, normalize, sources, supervisors, health, snapshot_writer?)`.
  - `start()`: consumer.start + supervisors start.
  - `stop()`: consumer stop → supervisors stop (cancel+disconnect) → health snapshot flush.
  - `run_until_stopped()` / `request_stop()`: event-driven lifecycle.
  - `build_collector_app(...)` — фабрика с passthrough normalizer (до B4).
  - `install_signal_handlers(app)`: SIGTERM/SIGINT → request_stop (AC-HLT-05).
- Создан `collector/__main__.py` — skeleton entrypoint:
  - `--snapshot` флаг для health JSON.
  - Dev noop sources (пустой рантайм до s06–s10).
  - SIGTERM → clean exit 0 (через handlers).
- Создан `tests/unit/test_health_snapshot.py` (TDD red→green):
  - 8 targeted: metrics bump/read, queue depths, aggregator update/snapshot/overwrite/ts, writer JSON + parent dir, aggregator stop clean.
  - Manual verification: snapshot JSON + counters + stop idempotent.
  - Targeted: 8 passed.
  - Regression: 151 passed (s01–s10 + s14).

## Файлы
- `apps/edge/collector/src/collector/health/metrics.py` (Создание)
- `apps/edge/collector/src/collector/health/aggregator.py` (Создание)
- `apps/edge/collector/src/collector/health/snapshot_writer.py` (Создание)
- `apps/edge/collector/src/collector/health/__init__.py` (Создание)
- `apps/edge/collector/src/collector/app.py` (Создание)
- `apps/edge/collector/src/collector/__main__.py` (Создание)
- `apps/edge/collector/tests/unit/test_health_snapshot.py` (Создание)

## Тесты
- **Runner note:** `PYTHONPATH=src .venv/bin/python -m pytest`. Async через `asyncio.run` (как в s04/s05).
- red: `ModuleNotFoundError: No module named 'collector.health.aggregator'`.
- cmd targeted: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_health_snapshot.py`
- итог targeted: **8 passed in 0.09s**.
- cmd regression: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/`
- итог regression: **151 passed in 0.88s** (s01–s10 + s14; без регрессий).

Покрытие (чекпоинты decompose s14):
- snapshot JSON обновляется — green ✓ (test_snapshot_writer_writes_json_file + manual).
- counters samples_in/out/errors/queue_depth — green ✓ (test_metrics_bump_and_read, test_metrics_queue_depths_are_setters, test_health_aggregator_update_source_and_snapshot).
- stop clean — green ✓ (test_health_aggregator_stop_is_safe).
- Aggregator перезаписывает source — green ✓ (test_health_aggregator_overwrites_source_on_update).
- Fresh ts — green ✓ (test_health_aggregator_snapshot_ts_is_fresh).

## §0.11 Integration
- Новых routes/keys/env/cols/migrations — нет. Шаг pure in-proc (health + app skeleton).
- HealthStatus (domain/models.py:75) → aggregator хранит по source_id; snapshot → list[HealthStatus].
- CollectorHealthSnapshot (domain/models.py:86) → aggregator.snapshot() → writer.write().
- RawConsumer.raw_depth / QueueSink.*_depth → set_queue_depths (потребители health).
- SourceSupervisor.stop() (s04) → CollectorApp.stop() вызывает (AC-HLT-04).
- Signal handlers → SIGTERM/SIGINT → app.request_stop() → exit 0 (AC-HLT-05 prep).
- Нет Redis/Kafka/broker (как в s05); in-proc только.
