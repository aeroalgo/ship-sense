# BACK BUGFIX — package paths and compose runtime

**Дата:** 2026-07-29  
**Статус:** completed

## Root cause

1. Pytest не добавлял `collector/src` и `emulator/src` в import path при запуске полного suite из корня.
2. Collector получал refs вида `maps/stub_*.yaml`, но bootstrap безусловно добавлял `maps_dir`, получая `/app/maps/maps/...`.
3. Writer image не содержал пакет `collector`, используемый моделями storage, и миграции выводили URL без установленного драйвера `psycopg2`.
4. Collector runtime после исправления путей загружал quality rules из `/app`, хотя они находятся в `/app/config`; compose также запускал конфликтующие dev sources, поэтому был добавлен smoke filter `aps_main`.

## Fix

- Добавлен `tool.pytest.ini_options.pythonpath` для обоих src-layout пакетов.
- Нормализовано разрешение map refs через `_resolve_map_path`; normalizer берет config directory от `sources_path`.
- MQTT compose `COLLECTOR_MAPS_DIR` приведён к `/app/maps`; обновлён unit contract.
- Storage image копирует collector src в `/app/collector` и задаёт `PYTHONPATH=/app:/app/collector`.
- Alembic migration URL использует `postgresql+psycopg`, соответствующий установленному драйверу.
- В compose collector задан `SHIPSSENSE_SMOKE_SOURCES=aps_main` для исключения дублирующего native-id в dev stub maps.

## Files

- `pyproject.toml`
- `tests/conftest.py`
- `apps/edge/collector/src/collector/runtime/bootstrap.py`
- `apps/edge/collector/tests/unit/test_mqtt_config.py`
- `apps/edge/storage/Dockerfile`
- `apps/edge/storage/__main__.py`
- `tests/storage/test_s17_integration.py`
- `docker-compose.yml`

## Verification

- `.venv/bin/pytest -q` — pass.
- `docker compose config -q` — pass.
- `docker compose ps` — db, writer, emulator, collector healthy.
- `git diff --check` по bugfix-файлам — pass.

## §0.11

- pytest package path ↔ `pyproject.toml` и root `tests/conftest.py`.
- map reference format `maps/...` ↔ collector `maps_dir` resolution.
- storage model imports ↔ Docker `COPY`/`PYTHONPATH`.
- Alembic URL ↔ installed `psycopg[binary]`.
- compose source filter ↔ duplicate native-id constraint.
