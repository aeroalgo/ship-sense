# [T-001 | s18 | emulator-dirt] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s18-emulator-dirt.md](../../plan/decompose-v1-p1-collector/s18-emulator-dirt.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic step; ScenarioRunner boundary задан CR-COL-03  
**Статус:** done

## Сделано

- Создан `ScenarioRunner` в `apps/edge/emulator/src/emulator/dirt/scenario_runner.py`.
- Добавлена YAML-загрузка сценариев с поддержкой `enabled`, `seed`, включения одного имени или списка имён и детерминированного `tick` поверх общего profile-driven generator.
- Реализованы value overlays: `signal_chatter`, `out_of_range`, `stuck_value`, `nan_inf`.
- Реализованы metadata hooks: `time_jump`, `tag_map_change`, `opc_bad_quality`.
- Реализованы transport hooks: `connection_drop`, `modbus_bad_frame`.
- Реализован `duplicate_delivery` как выдача двух одинаковых snapshot-доставок.
- Добавлены отдельные injector-модули-экспорты для каждого имени сценария в `dirt/injectors/`.
- Добавлены `config/scenarios.yaml`, `emulator/app.py` и `emulator/__main__.py`.
- В `app.py` добавлен небольшой `ScenarioGenerator`-adapter, чтобы protocol adapters s16/s17 продолжили получать интерфейс `profile` + `tick` без изменения их core API.

## Файлы

- `apps/edge/emulator/src/emulator/dirt/__init__.py`
- `apps/edge/emulator/src/emulator/dirt/scenario_runner.py`
- `apps/edge/emulator/src/emulator/dirt/injectors/base.py`
- `apps/edge/emulator/src/emulator/dirt/injectors/value.py`
- `apps/edge/emulator/src/emulator/dirt/injectors/__init__.py`
- `apps/edge/emulator/src/emulator/dirt/injectors/{chatter,connection_drop,out_of_range,stuck_value,time_jump,tag_map_change,bad_frame,nan_inf,duplicate,opc_bad_quality}.py`
- `apps/edge/emulator/config/scenarios.yaml`
- `apps/edge/emulator/src/emulator/app.py`
- `apps/edge/emulator/src/emulator/__main__.py`
- `apps/edge/emulator/tests/test_scenarios.py`

## TDD

- red: `PYTHONPATH=apps/edge/emulator/src pytest -q apps/edge/emulator/tests/test_scenarios.py` → `ModuleNotFoundError: No module named 'emulator.dirt'` до реализации.
- green: `PYTHONPATH=apps/edge/emulator/src pytest -q apps/edge/emulator/tests/test_scenarios.py` → **6 passed in 0.03s**.
- targeted regression: `PYTHONPATH=apps/edge/emulator/src pytest -q apps/edge/emulator/tests/test_scenarios.py apps/edge/emulator/tests/test_determinism.py` → **11 passed in 0.81s**.
- protocol regression: `PYTHONPATH=apps/edge/emulator/src pytest -q apps/edge/emulator/tests/test_modbus_server.py apps/edge/emulator/tests/test_opcua_server.py` → **5 passed in 5.96s**.
- syntax: `python -m compileall -q apps/edge/emulator/src` → exit 0.
- Полный suite не запускался: полный regression относится к BACK QA.

## Integration check (§0.11)

- [x] scenario names из YAML ↔ injector registry: все AC-I3-04..13 имена зарегистрированы.
- [x] profile `signal_id` selectors ↔ `native_ids`: value overlays применяются к каждому native ID выбранного signal.
- [x] generator snapshot ↔ s16/s17: `ScenarioGenerator` сохраняет `profile` + `tick`, используемые обоими read-only adapters.
- [x] metadata counterparts: timestamp/status/node filtering доступны protocol-facing hooks.
- [x] transport counterparts: connection drop и bad-frame predicates доступны adapter-facing hooks.
- [x] duplicate delivery ↔ downstream idempotency seam: `deliveries()` возвращает два равных snapshot при активном окне.
- [x] deterministic contract: одинаковые profile + generator seed + scenario definition дают одинаковые snapshots.
- [ ] фактическое закрытие TCP-сокета при `connection_drop` — hook predicate готов, wire в server lifecycle относится к следующему integration step s19/s20.
- [ ] фактическая порча Modbus PDU CRC/length — hook predicate готов, байтовый transport wire относится к s19/s22.
- [ ] runtime OPC UA `StatusCode` write и dynamic node creation — metadata hooks готовы, adapter wiring относится к s20/s22.

## Code review

- Read-only review requested after targeted verification; findings to be applied before BACK QA if they identify contract defects.
