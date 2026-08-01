# [T-005 | QA-1] BUGFIX — изоляция metadata ReportRun

**Дата:** 2026-08-01  
**Эпик:** `v1-p2-ship`  
**Источник:** [qa-20260801-v1-p2-ship.md](../../qa/v1-p2-ship/qa-20260801-v1-p2-ship.md) → QA-1  
**Статус:** completed

## Симптом

При импорте API-модели `ReportRun` в том же pytest-процессе, где выполняется storage contract, `apps.edge.storage.schemas.Base.metadata.tables` получает лишнюю таблицу `report_runs`. Проверка `tests/storage/test_schemas.py::test_storage_models_expose_expected_tables_and_columns` завершается assertion failure.

## Root cause

`apps/api/app/reports/models.py` импортировал декларативный `Base` из `apps.edge.storage.schemas` и регистрировал `ReportRun` в metadata edge-хранилища. Это нарушало границу доменов: SQLAlchemy добавляет таблицу наследника в metadata конкретного `DeclarativeBase`, поэтому cross-import загрязнял глобальный registry storage-моделей.

## Исправление

В `apps/api/app/reports/models.py` создан отдельный локальный `DeclarativeBase` для report-моделей. `ReportRun` больше не наследуется от edge storage `Base`, а миграция `007_report_runs.py` остаётся независимой: таблица создаётся явным DDL.

## Файлы

- `apps/api/app/reports/models.py`
- `tests/storage/test_schemas.py` — regression contract без изменения
- `migrations/versions/007_report_runs.py` — проверено, явный DDL сохранён

## Проверка

- `.venv/bin/pytest apps/api/tests/reports/test_engine_core.py tests/storage/test_schemas.py -q --tb=line` → `4 passed`
- `.venv/bin/pytest tests/storage/test_schemas.py -q --tb=line` → `2 passed`
- `.venv/bin/graphify update .` → граф обновлён

## Integration check

- [x] `ReportRun` metadata изолирована от edge storage metadata
- [x] `report_runs` DDL остаётся согласованным с моделью
- [x] storage table contract не расширен API-моделью
- [x] regression проверен импортом reports вместе со storage-тестом

## Следующая проверка

После исправления QA-1 требуется новая команда `BACK BUGFIX` для следующего отдельного blocker из QA Fix plan либо повторный `BACK QA v1-p2-ship` после закрытия QA-2–QA-4.
