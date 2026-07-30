# [T-001 | s26 | runtime-gaps-r1-r3] IMPLEMENT

**Plan ID:** v1-p1-collector (gap-close v1-p1-edge-runtime-smoke)
**Дата:** 2026-07-27
**Уровень:** L3
**Статус:** done

## Сделано

- R-1: `SnapshotWriter` получил lifecycle loop; `CollectorApp.start()` пишет running snapshot сразу и обновляет его периодически, а `stop()` корректно останавливает loop и пишет stopped snapshot.
- R-2: production entrypoint больше не создаёт noop sources/`NullSink`; runtime bootstrap читает YAML, env `SHIPSSENSE_WRITER_ENDPOINT`, source filter, строит Modbus/OPC UA factories, supervisors, normalizer и `IpcCanonicalSink`.
- Registry принимает class или callable factory.
- R-3: OPC UA emulator хранит объявленный `VariantType` для каждой node и передаёт typed/coerced values в `write_value()`, устраняя `Double→Float` и `Int64→Int16/Int32` mismatch.

## Файлы

- `apps/edge/collector/src/collector/runtime/__init__.py`
- `apps/edge/collector/src/collector/runtime/endpoints.py`
- `apps/edge/collector/src/collector/runtime/bootstrap.py`
- `apps/edge/collector/src/collector/__main__.py`
- `apps/edge/collector/src/collector/app.py`
- `apps/edge/collector/src/collector/health/snapshot_writer.py`
- `apps/edge/collector/src/collector/core/supervisor.py`
- `apps/edge/collector/src/collector/plugins/registry.py`
- `apps/edge/emulator/src/emulator/protocols/opcua_server.py`
- `apps/edge/collector/tests/unit/test_runtime_gaps.py`

## Тесты

- cmd: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_runtime_gaps.py apps/edge/collector/tests/unit/test_health_snapshot.py apps/edge/collector/tests/unit/test_plugin_registry.py apps/edge/emulator/tests/test_opcua_server.py -q`
- итог: **29 passed in 5.96s**
- cmd: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/python -m compileall -q apps/edge/collector/src apps/edge/emulator/src`
- итог: **PASS**

## Integration check

- [x] env `SHIPSSENSE_WRITER_ENDPOINT` → parser → `IpcCanonicalSink`
- [x] source config → plugin factory → connector → supervisor
- [x] health snapshot lifecycle → compose file healthcheck path
- [x] OPC UA declared datatype → typed update
- [ ] full compose smoke / writer frame count — перенести в BACK QA
