# [T-001 | s22 | integration-dirty-t3] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s22-integration-dirty-t3.md](../../plan/decompose-v1-p1-collector/s22-integration-dirty-t3.md)
**Дата:** 2026-07-27
**Уровень:** L2 по atomic integration test step
**Статус:** done

## Сделано
- Создан `apps/edge/collector/tests/integration/test_normalizer_dirty.py` — интеграционная матрица **все dirt-сценарии I3 → Quality через B4** (AC-I3-04..13, AC-B4-13).
- Связывает I3 (dirt injectors эмулятора, s18) с B4 (Normalizer pipeline: `Normalizer` + `QualityEngine.from_yaml(quality_rules.yaml)` + `UnitConverter(UnitRules())` + `EventDetector`). Не поднимает live TCP (это удел s19/s20/s21) — гоняет реальный `Normalizer.process()` на синтезированных `RawSample`, воспроизводящих сигнатуры грязи, как их кодируют connectors на пути из эмулятора (`opcua.<Status>`, `modbus.<token>`, `nan/inf`, out-of-range, stale timestamp, неизвестный NodeId, дубликат).
- Покрытие матрицы (`QUALITY_MATRIX` parametrize):
  - AC-I3-05 connection_drop → `modbus.timeout` → **bad**
  - AC-I3-12 modbus_bad_frame → `modbus.exception.4` → **bad**
  - AC-I3-13 opc_bad_quality → `opcua.BadNoCommunication` → **bad**
  - AC-I3-08 nan_inf → `nan`/`inf` → **bad**, value=null (AC-B4-08)
  - AC-I3-06 out_of_range → ± от диапазона → **uncertain**, значение сохраняется (AC-B4-07)
  - AC-I3-07 stuck_value → устаревший source_ts → **stale** (stale_threshold_sec=3.0)
  - AC-I3-09 time_jump past → возрастающий age → **stale**; future → **good** (не stale, age<0)
  - baseline clean → **good**
- Поведенческие сценарии (не quality-маппинг) — отдельными тестами:
  - AC-I3-10 tag_map_change: неизвестный NodeId → **quarantine**, tag_id fallback=native_id, value=null, unit=unknown.
  - AC-I3-11 duplicate_delivery: второй сэмпл с тем же `native_id+source_ts` дропается (idempotent B4, возвращает `None`).
  - AC-I3-04 signal_chatter: серия быстрых discrete-change (`bool`) не роняет normalizer, эмитит discrete events через `EventDetector`.
- **AC-B4-13 (главное):** `test_all_dirt_scenarios_do_not_raise` — полная матрица грязи, ни одного uncaught exception в worker-эквиваленте.

## Файлы
- `apps/edge/collector/tests/integration/test_normalizer_dirty.py` (создание, только тест)

## Реализация (prod-код)
- **Не потребовалась.** `code_surface: test` — шаг создаёт только тест. Существующий B4 (`Normalizer.process` s13 + `QualityEngine.evaluate` s11 + `_encode_value` nulling + dedup) уже обеспечивает проверяемые quality-маппинги и устойчивость к грязи. Прод-багов, как в s20, этот тест не вскрыл — все 20 проверок зелёные на первом же GREEN после исправления двух багов в самом тесте (см. TDD).

## TDD
- red (1-я итерация): все 21 падают на `FileNotFoundError: 'apps/edge/collector/config/quality_rules.yaml'` при запуске из `apps/edge/collector/`. Причина — относительный путь к YAML зависит от cwd (unit-тесты используют тот же путь и гоняются из корня репо).
- fix: запуск targeted из **корня репо**: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/pytest` (canonical path, как для всего suite collector-а). Относительный путь в тесте оставлен — он совпадает с `tests/unit/test_normalizer.py`, единый convention.
- red (2-я итерация): `test_connection_drop_and_bad_frame_null_value` падал — `assert sample is not None`. Причина: цикл гонял 3 разных `native_quality`, но одинаковый `native_id+source_ts` → B4 корректно дропал дубликаты (это AC-I3-11, фича). И `test_tag_map_change_unknown_node_is_quarantined` — `TypeError: _normalizer() takes 0 positional arguments but 1 was given`.
- fix: (1) разношу `source_ts` по итерациям (`EDGE_NOW + timedelta(i)`); (2) `_normalizer(entries={})` вместо positional. Это правки **теста**, не прод-кода.
- green: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src pytest -q apps/edge/collector/tests/integration/test_normalizer_dirty.py` → **20 passed in 0.22s**.
- Regression: `tests/integration/` + `tests/unit/test_normalizer.py` + `tests/unit/test_quality_engine.py` → **61 passed in 8.73s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.

## Integration check (§0.11)
- [x] `QualityEngine.from_yaml("apps/edge/collector/config/quality_rules.yaml")` ↔ файл существует, валиден (s11 canon).
- [x] `modbus.timeout` / `modbus.client_error` / `modbus.exception.4` ↔ `quality_rules.yaml` modbus.map (bad/uncertain по правилам).
- [x] `opcua.BadNoCommunication` ↔ quality_rules opcua severity_class `bad` (префикс Bad* → bad).
- [x] `stale_threshold_sec: 3.0` ↔ stale-сценарии (age>3 → stale).
- [x] `range: {min:0, max:100}` ↔ out_of_range (uncertain, value kept) — AC-B4-07.
- [x] `UnitConverter(UnitRules())` — default rules, `convert(None)` passthrough для bad-quarantined value.
- [x] `EventDetector()` ↔ discrete chatter эмитит events без падения.
- [x] targeted pytest green; regression green.

## Чекпоинт верификации (step)
- [x] матрица scenario→expected quality покрыта (`QUALITY_MATRIX` parametrize + поведенческие тесты)
- [x] нет uncaught exceptions в worker (`test_all_dirt_scenarios_do_not_raise`)
- [x] Normalizer не падает на NaN/Inf/out-of-range/stale/duplicate/unknown-tag (AC-B4-13)
