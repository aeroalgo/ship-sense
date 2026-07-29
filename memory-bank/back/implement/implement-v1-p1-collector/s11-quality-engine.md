# s11 — Quality engine YAML rules + stale + OPC/Modbus mapping IMPLEMENT

**Дата:** 2026-07-27
**Уровень:** L3 (один сервисный модуль + connector-контракт правки + YAML + TDD)
**Статус:** done

**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md) (§7.1 Quality, §14.2 quality rules YAML)
**Decompose:** [s11-quality-engine.md](../../plan/decompose-v1-p1-collector/s11-quality-engine.md)
**Creative:** [creative-collector-quality-mapping.md](../../creative/creative-collector-quality-mapping.md) — CR-COL-04 done
**AC:** AC-B4-04 (5 quality reachable), AC-B4-07 (out-of-range, value kept), AC-B4-08 (NaN/Inf → bad), AC-B4-12 (YAML rules), AC-B3-06 (StatusCode → Quality)

## Сделано

QualityEngine (pure core + YAML-canonical rules) + connector-side structured token contract (`opcua.<name>` / `modbus.<token>`).

- `core/quality_engine.py`: `QualityRules` (pydantic, validates YAML at load) + sub-models (`OpcUaRules`/`ModbusRules`/`ValueRules`/`RangeRules`) + `EvalResult(quality,value,reason)` dataclass + `QualityEngine.evaluate(raw, map_entry, now) → EvalResult` + `from_yaml` classmethod + standalone pure helpers `map_opcua_status(name, rules)` / `map_modbus_exception(token, rules)`.
- `config/quality_rules.yaml`: canon правил (OPC severity-class + 5 overrides, Modbus 9 токенов + safe defaults, NaN/Inf=bad, range=uncertain, stale_threshold_sec=3.0, unknown_native_quality=good).
- Rule priority fixed в code (не YAML): **quarantine > native_quality > NaN/Inf > range > stale > good** (creative §7).
- Value encoding: bad/quarantine → null; uncertain/stale/good → value (creative §4, AC-B4-07).
- Connector token contract:
  - `plugins/modbus/connector.py`: error-path `native_quality=str(e)` → `modbus.<token>` через `_modbus_error_token`/`_modbus_error_kind` (timeout | client_error | exception[.<code>]). 3 места: `read()`, `_poll_group()` per-register decode, `_poll_group()` group-level.
  - `plugins/opcua/subscription.py`: `_make_raw_sample` `native_quality=str(status)` → `opcua.<StatusName>` (`getattr(status,"name",None) or str(status)`).
  - `plugins/opcua/connector.py`: `read()` error-path `native_quality=str(e)` → `opcua.exception` через `_opcua_error_token`.

TDD vertical slices (creative §14.3, 1 test → 1 impl): GOOD → NaN/Inf → range → stale → quarantine → Modbus tokens → OPC severity/overrides → priority pairs → YAML reload → value encoding → standalone helpers. RED confirmed (ModuleNotFoundError) → GREEN.

## Файлы

**Создание:**
- `apps/edge/collector/src/collector/core/quality_engine.py`
- `apps/edge/collector/config/quality_rules.yaml`
- `apps/edge/collector/tests/unit/test_quality_engine.py`

**Правки (connector-side contract):**
- `apps/edge/collector/src/collector/plugins/modbus/connector.py` (+ `_modbus_error_token`/`_modbus_error_kind` helpers, `+ import ModbusException`)
- `apps/edge/collector/src/collector/plugins/opcua/subscription.py` (`_make_raw_sample` token)
- `apps/edge/collector/src/collector/plugins/opcua/connector.py` (`+ _opcua_error_token` helper, `read()` error path)
- `apps/edge/collector/tests/unit/test_modbus_connector.py` (asserts: `modbus.timeout` token; + 1 new read-error test)

## Тесты

- cmd: `PYTHONPATH=src python3 -m pytest tests/unit/test_quality_engine.py -q`
- итог: **30 passed** (engine slices + standalone helpers + canon YAML load)
- regression cmd: `PYTHONPATH=src python3 -m pytest tests/ -q`
- regression итог: **182 passed** (connector-правки не сломали существующие тесты)

> Запуск: src-layout, пакет не installed → `PYTHONPATH=src` (нет editable install, нет pytest.ini pythonpath). Полный suite — регрессионная проверка затронутых модулей; canonical полный QA = BACK QA.

## Integration check (§0.11)

- [x] native_quality token producers ↔ engine `_map_native` dispatch: `opcua.<name>` ↔ `map_opcua_status`; `modbus.<token>` ↔ `map_modbus_exception`. Все producer-сайты (3 modbus + 2 opcua) замкнуты.
- [x] YAML path `config/quality_rules.yaml` ↔ `QualityEngine.from_yaml` (canon load test green).
- [x] defaults в pydantic-моделях = canon YAML (тесты на `QualityRules()` без YAML проходят).
- [ ] **Wiring в NormalizerWorker (s13)** — вне scope s11 (creative §10.3: «в s11 только класс + YAML, без wiring»). Engine instance не создаётся в pipeline. → s13.
- [n/a] env / DB / events — модуль pure, без I/O.

## Known / out-of-scope

- `modbus/connector.py:80` `native_quality="unknown_tag"` (sync `read()`, native_id не в карте) — **pre-existing**, не моя правка. Токен не prefixed → engine сопоставит с `unknown_native_quality: good` default. Семантически = quarantine, но quarantine детектит NormalizerWorker через `map_entry=None` (creative §8), а не connector sync-путь. Out of CR-COL-04/s11 scope; отметить для s13/bуйти в B2 review.
- Modbus `exception.<code>` code-извлечение: в этой pymodbus-версии нет `ExceptionResponse.code`; protocol `ModbusException("modbus exception: {resp}")` → токен `modbus.exception` (без code), покрывается `unknown_exception: bad` safe default. Per-code mapping (slice 7 `exception.5`) достижим через прямой токен-тест + standalone helper.
