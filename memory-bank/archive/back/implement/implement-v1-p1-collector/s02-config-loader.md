# T-001 | s02 | Config loader IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s02-config-loader.md](../../plan/decompose-v1-p1-collector/s02-config-loader.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-26  
**Уровень:** L2  
**Статус:** done

## Skills

- `tdd`
- `python-testing-patterns`
- `modern-python`
- `verification-before-completion`
- `requesting-code-review`

## Сделано

- Добавлены Pydantic v2-модели конфигурации: `SourceConfig`, `PollConfig`, `PollGroup`, `SubscribeConfig`, `SecurityConfig`, `TagMapEntry`, `CollectorSettings`.
- Реализован YAML loader для sources и tag maps с env override через `COLLECTOR_SOURCES_PATH` и `COLLECTOR_MAPS_DIR`.
- Реализован fail-fast validator: поддерживаемые протоколы, обязательный poll/subscribe, map refs и дубли `native_id`.
- Добавлен CLI `python -m collector.config validate`.
- Добавлены dev sources и stub maps: APS map содержит 62 тега и 9 datatype, включая OPC node map; SKT GEU — subset.
- Добавлена runtime-зависимость `PyYAML>=6.0`.

## Файлы

- `apps/edge/collector/src/collector/config/models.py`
- `apps/edge/collector/src/collector/config/loader.py`
- `apps/edge/collector/src/collector/config/validator.py`
- `apps/edge/collector/src/collector/config/__init__.py`
- `apps/edge/collector/src/collector/config/__main__.py`
- `apps/edge/collector/config/sources.dev.yaml`
- `apps/edge/collector/maps/stub_aps_main.yaml`
- `apps/edge/collector/maps/stub_skt_geu.yaml`
- `apps/edge/collector/maps/stub_aps_main_nodes.yaml`
- `apps/edge/collector/tests/unit/test_config_validator.py`
- `apps/edge/collector/pyproject.toml`

## Тесты

- red: `PYTHONPATH=apps/edge/collector/src pytest -q apps/edge/collector/tests/unit/test_config_validator.py` → `ModuleNotFoundError: No module named 'collector.config'`.
- cmd: `PYTHONPATH=apps/edge/collector/src python -m collector.config validate` с `COLLECTOR_SOURCES_PATH=apps/edge/collector/config/sources.dev.yaml` и `COLLECTOR_MAPS_DIR=apps/edge/collector/maps`.
- итог CLI: `config valid: 3 sources`, exit 0.
- cmd: `PYTHONPATH=apps/edge/collector/src pytest -q apps/edge/collector/tests/unit/test_config_validator.py apps/edge/collector/tests/unit/test_domain_models.py`
- итог: `13 passed in 0.11s`.

## Integration check

- [x] `COLLECTOR_SOURCES_PATH` и `COLLECTOR_MAPS_DIR` wired в loader/validator и покрыты тестом.
- [x] `tag_map_ref`/`nodes_ref` разрешаются относительно maps directory.
- [x] `native_id` duplicates fail before connector startup.
- [x] Нет storage keys, DB columns или event handlers в этом шаге.

## Graphify

- `.venv/bin/graphify query` выполнен, но `graphify-out/graph.json` отсутствует.
- FINISH update невозможно без graph input; fallback — проверить файлы и тесты вручную.

## Статус требований

- [x] AC-CFG-01 — sources dev config содержит `aps_main`, `aps_main_opcua`, `skt_geu`.
- [x] AC-CFG-02 — APS stub map содержит ≥50 representative tags всех плановых datatype.
- [x] AC-CFG-03 — validator CLI работает через `python -m collector.config validate`.
- [x] AC-CFG-04 — env overrides меняют пути sources/maps.
- [x] AC-B1-09 — duplicate native_id даёт ConfigError и ненулевой CLI-путь.
- [ ] Полный suite — оставлен для `BACK QA`.
