# [T-008 | v1-p1-mqtt-smoke] REVIEW

**Дата:** 2026-07-29
**Reviewer:** BACK QA
**Verdict:** pass

## Scope

- task: T-008 MQTT compose smoke gap-close
- files: `scripts/smoke-mqtt-stack.sh`, `docker-compose.yml`, `apps/edge/collector/src/collector/domain/interfaces.py`, collector config/plugin import path
- modes: `single`, `dual`, `events`

## Checks

- [x] `bash -n scripts/smoke-mqtt-stack.sh` — OK
- [x] `docker compose --profile mqtt-dev config` — exit 0
- [x] `docker compose --profile mqtt-dev config --services` — includes `mosquitto`, `emulator-mqtt`, `collector-mqtt`, `writer`
- [x] `python3 -m compileall -q apps/edge/collector/src apps/edge/emulator/src` — OK
- [x] MQTT single smoke — exit 0
- [x] MQTT dual smoke — exit 0
- [x] MQTT events smoke — exit 0
- [x] MQTT sigterm smoke — exit 0
- [x] compose/config/syntax/compile checks — exit 0
- [x] backend fast suite — 327 passed
- [x] MQTT integration — 2 passed
- [x] emulator integration — 2 passed
- [x] security spot-check — no new high-confidence issue established; dev ACL intentionally allows readwrite on `shipsense/#`

## Issues

| ID | sev | file | msg |
|----|-----|------|-----|
| R-1 | resolved | `apps/edge/collector/src/collector/config/validator.py:37` | Lazy `MqttChannelMap` import removes the circular import; compose smoke and MQTT integration pass. |
| R-2 | resolved | `scripts/smoke-mqtt-stack.sh:32-39` | All four documented modes now exit 0. |
| R-3 | note | `apps/edge/collector/tests/conftest.py` / environment | Full unfiltered root invocation lacks package `PYTHONPATH`; validated backend suites with explicit source paths. |

## Evidence

```text
.venv/bin/pytest — collection fails without PYTHONPATH (`collector`/`emulator` imports).
.venv/bin/pytest with PYTHONPATH, excluding soak — 327 passed.
MQTT integration — 2 passed; emulator integration — 2 passed.
scripts/smoke-mqtt-stack.sh single|dual|events|sigterm — all exit 0.
```

```text
.venv/bin/graphify query ... -> MQTT graph context returned; no graph update because QA made no code changes.
bash -n scripts/smoke-mqtt-stack.sh -> exit 0
docker compose --profile mqtt-dev config -> exit 0
PYTHONPATH=apps/edge/collector/src python -c 'import collector.plugins.mqtt.connector'
ImportError: cannot import name 'BaseSourceConnector' from partially initialized module collector.domain.interfaces
scripts/smoke-mqtt-stack.sh single (clean container run)
FAIL: writer did not receive samples within 30s
collector log: ImportError ... BaseSourceConnector ... circular import
PYTHONPATH=... pytest -q apps/edge/collector/tests -> collection blocked by ModuleNotFoundError: pymodbus
PYTHONPATH=... pytest -q apps/edge/emulator/tests -> collection blocked by ModuleNotFoundError: pymodbus
python3 -m compileall -q ... -> exit 0
````

## Blockers

- Fix the collector package circular import before rerunning compose smoke.
- Install/use the repository's intended backend dependencies (including `pymodbus`) before full suite verification.
- Rerun `single`, `dual`, and `events` sequentially after cleanup; do not run them concurrently because compose uses fixed container names.

## Verdict

**BLOCKED / FAIL.** Harness syntax and compose wiring validate, but no end-to-end MQTT sample, dual health, or lifecycle event can be accepted while collector startup fails.
