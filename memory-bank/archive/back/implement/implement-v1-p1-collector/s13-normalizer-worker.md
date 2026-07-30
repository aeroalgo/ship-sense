# [T-001 | s13 | normalizer-worker] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s13-normalizer-worker.md](../../plan/decompose-v1-p1-collector/s13-normalizer-worker.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-27
**Уровень:** L2
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s13-normalizer-worker.md`

## Сделано

- Создан `Normalizer`: raw → `TelemetrySample` с map lookup, QualityEngine, UnitConverter, UTC timestamps и dedup по `(native_id, source_ts)` независимо от источника.
- Добавлен quarantine для неизвестного native_id; ошибки нормализации логируются и возвращают `None`, не роняя consumer loop.
- Создан `EventDetector`: минимальный Q4 stub для discrete value changes; `Normalizer.drain_events()` выдаёт накопленные Event.
- `RawConsumer` теперь корректно пропускает dedup/ошибочные `None` samples.
- Dedup проверен отдельным тестом для одинакового native_id/source_ts из Modbus и OPC UA: второй sample отбрасывается.
- Создан `utc_now()` с aware UTC datetime.

## Файлы

- `apps/edge/collector/src/collector/core/normalizer.py`
- `apps/edge/collector/src/collector/core/event_detector.py`
- `apps/edge/collector/src/collector/util/time.py`
- `apps/edge/collector/src/collector/core/raw_consumer.py`
- `apps/edge/collector/tests/unit/test_normalizer.py`

## Тесты

- red: `ModuleNotFoundError: No module named 'collector.core.event_detector'`.
- cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_normalizer.py -q`
- итог: **7 passed**.

## Integration check

- [x] `TagMapEntry` → lookup by `RawSample.native_id`; Modbus/OPC share same map shape.
- [x] `QualityEngine.evaluate` → `UnitConverter.convert` → `TelemetrySample`.
- [x] `edge_ts` always from `utc_now`/injected clock; `source_ts` falls back to edge timestamp.
- [x] duplicate `(source_id, native_id, source_ts)` produces one canonical sample.
- [x] `RawConsumer` does not write `None` samples; its loop remains alive for normalizer failures.
- [x] Events are emitted as in-memory side effects; no handler/DB/route exists in this scope.
- [n/a] env / DB / route / migration / column — pure collector service, no new external contract.

## Почему

s13 реализован минимально по AC-B4-01/02/05/06/10/11/13; полноценный event sink wiring и dirty integration остаются для следующих шагов.

## Ограничения

- `Normalizer` хранит seen keys/events in-memory; lifecycle reset = новый экземпляр.
- Event detector поддерживает только discrete datatype changes; полноценный Q4 event grammar вне s13.
- Unit conversion использует map unit как source/target в отсутствие отдельного raw-unit поля в `RawSample`; per-tag calibration работает через scale/offset.
- Ошибки процесса логируются и пропускают sample; consumer loop не падает.

## Проверка

- [x] targeted normalizer tests green
- [ ] full collector suite — BACK QA
- [ ] static/lint checks — не запускались отдельным шагом
