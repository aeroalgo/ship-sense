# BACK REFACTOR session — r01 scaffold apps/api

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r01`
- **Дата:** 2026-07-30
- **Behavior freeze:** IPC wire, Quality/EventSeverity values, DB ORM schema и семантика коннекторов не затрагивались.

## Реализация

- Создан пакет `apps/api/app` по FastAPI template layout.
- Добавлены `create_app()` и module-level `app` в `apps/api/app/main.py`.
- Добавлен no-op lifespan и API router, смонтированный с `/api`.
- Добавлен stub `GET /api/health` с ответом `{status: ok}`.
- Добавлены каркасы settings и пустые feature/core packages для последующих шагов.
- В `pyproject.toml` добавлены `apps/api` в `pythonpath` и `apps/api/tests` в `testpaths`.
- Не создавался `apps/edge/api`; бизнес-эндпоинты T-003 не добавлялись.

## Верификация / тесты

- RED до реализации: `.venv/bin/pytest apps/api/tests/api/test_health_stub.py -q --tb=line` → `ModuleNotFoundError: No module named 'app'`.
- GREEN после реализации: `.venv/bin/pytest apps/api/tests -q --tb=line` → `1 passed`.
- Поведение проверено через ASGI public interface: `/api/health` и `/openapi.json`.

## Статус

`completed`
