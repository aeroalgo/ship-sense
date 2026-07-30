# [T-001 | s15 | emulator-tag-model] IMPLEMENT

**Plan ID:** v1-p1-collector
**Decompose step:** [s15-emulator-tag-model.md](../../plan/decompose-v1-p1-collector/s15-emulator-tag-model.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-27
**Уровень:** L2 по atomic step; universal architecture задана CR-COL-03
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s15-emulator-tag-model.md`

## Сделано

- Создан profile-driven `TagGenerator` с публичным контрактом `tick(t) -> dict[native_id, value]`.
- Профиль загружается один раз через YAML loader; YAML parsing не выполняется в tick.
- Реализованы whitelisted generator kinds: `constant`, `random_walk`, `periodic`, `discrete`, `correlated`.
- Реализована топологическая обработка driver graph с понятными ошибками для неизвестного driver и циклов.
- Реализованы стабильные per-signal noise substreams на основе `(seed, profile_id, signal_id, tick, stream)` через стабильный BLAKE2b digest; порядок YAML не влияет на значения.
- Созданы generic correlation primitive и thin helper `correlate_rpm_temp_pressure`.
- Создан чистый bounded UTC-independent `daily_factor`.
- Создан `tags_stub.yaml` с 586 сигналами, двумя protocol-neutral native IDs на сигнал (Modbus и OPC UA), диапазонами и representative APS drivers.

## Файлы

- `apps/edge/emulator/src/emulator/__init__.py`
- `apps/edge/emulator/src/emulator/tag_model.py`
- `apps/edge/emulator/src/emulator/physics/__init__.py`
- `apps/edge/emulator/src/emulator/physics/correlations.py`
- `apps/edge/emulator/src/emulator/physics/daily_patterns.py`
- `apps/edge/emulator/config/tags_stub.yaml`
- `apps/edge/emulator/tests/test_determinism.py`

## Тесты

- red: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_determinism.py` → `ModuleNotFoundError: No module named 'emulator.physics.correlations'`.
- green: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_determinism.py` → **5 passed in 1.15s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.

## Integration check

- [x] protocol-neutral output: один snapshot содержит native IDs, пригодные для будущих Modbus и OPC UA adapters.
- [x] profile loader принимает canonical `profile + signals` schema и валидирует уникальность signal IDs/native IDs и driver references.
- [x] s16/s17 могут потреблять один `TagGenerator` и общий snapshot без physics imports.
- [x] s18 может ссылаться на `signal_id`; model не содержит transport dirt или protocol server.
- [n/a] storage keys / env vars / DB columns / migrations / routes — pure emulator model, внешних контрактов нет.
