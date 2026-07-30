# BACK REFACTOR — r02 move canonical models

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r02`
- **Дата:** 2026-07-30
- **Behavior freeze:** IPC wire, Quality/EventSeverity values, DB ORM schema и семантика коннекторов сохранены.

## Реализация / Файлы

- Созданы `apps/api/app/telemetry/models.py` с каноническими `Quality` и `TelemetrySample`.
- Созданы `apps/api/app/events/models.py` с каноническими `EventSeverity` и `Event`; `Quality` импортируется из telemetry-модуля.
- `collector.domain.models` разделён на `collector.domain.raw_models` (`RawSample`, `RawTagDescriptor`) и `collector.domain.health_models` (`SourceState`, `HealthStatus`, `CollectorHealthSnapshot`). Старый `models.py` удалён.
- `collector.domain.__init__` экспортирует только Raw*/health и domain errors; canonical types больше не объявляются и не реэкспортируются из collector.
- Collector core, sinks, interfaces и MQTT lifecycle/mapper переподключены к `app.telemetry.models` / `app.events.models` и локальным Raw*/health-модулям.
- Storage repositories/writer и pipeline/storage tests переподключены к `app.*` canonical models.
- В `collector.domain.interfaces` application-only imports помещены под `TYPE_CHECKING`, чтобы изолированный импорт collector domain не требовал API package на runtime.

## Верификация / Тесты

- Before baseline: `.venv/bin/pytest apps/edge/collector/tests tests/storage tests/pipeline -q --tb=line` → `373 passed, 9 deselected, 1 warning`.
- After refactor: `.venv/bin/pytest apps/edge/collector/tests tests/storage tests/pipeline -q --tb=line` → `373 passed, 9 deselected, 1 warning`.
- Изолированный импорт: `PYTHONPATH=apps/edge/collector/src .venv/bin/python -c 'import collector.domain.interfaces'` → PASS после переноса app imports под `TYPE_CHECKING`.
- `rg` по Python-коду не находит imports из `collector.domain.models` или `apps.edge.collector.src.collector.domain.models`.
- `.venv/bin/graphify update .` → graph rebuilt: 3125 nodes, 6549 edges.

## Статус

`completed`
