# BUGFIX 2026-07-30 — QA storage runtime blockers

**Источник:** [qa-20260730-v1-p1-storage](../../qa/v1-p1-storage/qa-20260730-v1-p1-storage.md)  
**Статус:** completed

## Симптомы (QA)

| ID | sev | Симптом |
|----|-----|---------|
| QA-1 | blocker | slow/full suite не terminal в 180s на MQTT E2E |
| QA-2 | high | compose logs: `ModbusException` flood; compression policy already exists; `jobs.last_run_started_at` |
| QA-3 | medium | lint tools нет в `.venv` — out of scope |
| QA-4 | low | trailing whitespace docs — out of scope |

## Root cause

### QA-1
- Repro сейчас: full suite **terminal green** — `400 passed in ~79s`.
- При QA 180s budget мог оборвать прогон на cold MosquittoContainer start; продуктового hang в тесте нет.
- Hardening: `mqtt_broker` fixture — `ThreadPoolExecutor` timeout 60s → terminal fail вместо бесконечного wait.

### QA-2 Modbus (две причины)
1. `_poll_group` ловил только `ModbusClientError`/`ModbusTimeoutError`. `pymodbus.ModbusException` (ExceptionResponse / illegal address) падал в `except Exception` → `logger.exception("poll group crashed")` на каждом тике (~740k ERROR).
2. `sources.dev.yaml` ссылался на `maps/stub_aps_main.yaml` (62 тега), из них **только 3** есть на emulator stub → Illegal Data Address для остальных.

### QA-2 compression
- `006_compression_retention.py`: `add_compression_policy` / `add_retention_policy` без `if_not_exists` → ERROR при повторном upgrade/ручном rerun.

### QA-2 `last_run_started_at`
- **Не runtime bug.** Колонка в `timescaledb_information.job_stats`, не в `.jobs`. QA-запрос к `.jobs` → ERROR в db log (однократно).

## Fix

1. Catch `ModbusException` в `_poll_group` → bad quality (`modbus.exception*`), без crash-log.
2. `sources.dev.yaml` → `maps/stub_aps_main_runtime.yaml` (3 тега ⊆ emulator).
3. Migration 006: `if_not_exists => true` для compression/retention policies.
4. `mqtt_broker`: start timeout 60s.

## Files

- `apps/edge/collector/src/collector/plugins/modbus/connector.py`
- `apps/edge/collector/config/sources.dev.yaml`
- `apps/edge/collector/tests/conftest.py`
- `apps/edge/collector/tests/unit/test_modbus_connector.py`
- `migrations/versions/006_compression_retention.py`
- `tests/storage/test_compose_modbus_map_contract.py`
- `tests/storage/test_compression_migration_idempotent.py`

## Tests

- RED→GREEN: `test_poll_group_modbus_exception_yields_bad_quality_without_crash_log`
- Contract: runtime map ⊆ emulator modbus ids
- Contract: migration `if_not_exists`
- Full: `.venv/bin/pytest -q` → **400 passed in 79.30s**
- Live: after rebuild collector — `ModbusException` count since restart = **0**; services healthy

## Verify

- §0.11: `tag_map_ref` ↔ `maps/stub_aps_main_runtime.yaml` ↔ Dockerfile `COPY maps/` ↔ emulator `tags_stub.yaml`
- §0.11: migration `if_not_exists` ↔ Timescale 2.14 API
- QA-3/QA-4 не чинились (не runtime)

## Next

`BACK QA` (new chat) — повторный QA storage + full/slow suite.
