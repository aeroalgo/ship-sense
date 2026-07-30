# BACK BUGFIX — emulator Modbus SimData overlap

**Дата:** 2026-07-27  
**Блокер:** `docker compose up` edge-stack — emulator crash при старте  
**Статус:** done

## Симптом

`TypeError: SimData address 5 is overlapping!` в `modbus_server.py:_build_context` при загрузке `tags_stub.yaml` (586 сигналов). Воспроизводится локально в venv, не Docker-специфика.

## Root cause

`_build_context` (s16) создавал **один `SimData` на сигнал**. В `tags_stub.yaml` input-регистры плотно упакованы: `float32` на `41004` занимает регистры 4–5, следующий `int16` на `41005` — регистр 5. Адреса **намеренно перекрываются** (583 регистра, span 4–586, gaps=0). `pymodbus.SimDevice` (3.14.0) отвергает перекрывающиеся `SimData` при `__post_init__`.

В integration-тестах не проявлялось — там малый profile (3 тега, непересекающиеся адреса).

## Fix

Слияние всех размещений сигналов в **единый register image** на блок (holding/input) через `_build_register_image()`, один `SimData` на блок. `_update_snapshot` пересобирает image и патчит runtime block целиком.

## Файлы

- `apps/edge/emulator/src/emulator/protocols/modbus_server.py` — `_build_register_image`, merge logic
- `apps/edge/emulator/tests/test_modbus_server.py` — regression на `tags_stub.yaml`

## TDD

- red: `test_build_context_accepts_full_tags_stub_profile` → `TypeError: SimData address 5 is overlapping!`
- green: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_modbus_server.py apps/edge/emulator/tests/test_determinism.py` → **9 passed**

## Handoff

- **Done:** emulator `_build_context` overlap fix — полный `tags_stub.yaml` стартует без crash.
- **Files:** `modbus_server.py`, `test_modbus_server.py`.
- **Tests:** emulator modbus + determinism — **9 passed**.
- **Next:** `BACK QA` — полный collector/emulator regression (T-001); затем `docker compose up` edge-stack smoke.
- **New chat:** yes.
