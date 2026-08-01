# BACK REFACTOR — r06 migrations stub + ORM policy

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r06`
- **Дата:** 2026-07-30
- **Behavior freeze:** storage ORM schema, repository-level Alembic entrypoint, API/IPC contracts и runtime semantics не изменялись.
- **Scope:** зафиксирована phase-1 ORM/migrations policy; добавлен неактивный API migrations scaffold.
- **code_changed:** yes

## Реализация / Файлы

- Обновлён `apps/api/README.md`:
  - `apps/edge/storage/schemas.py` остаётся владельцем SQLAlchemy tables и `Base.metadata`.
  - активной Alembic chain остаётся корневой `migrations/`, настроенный через `alembic.ini`.
  - `apps/api/migrations/` явно обозначен как зарезервированный неактивный scaffold без DDL ownership.
  - перенос storage Alembic chain и второй `DeclarativeBase` явно отнесены к non-goal фазы.
- Создан `apps/api/migrations/env.py` как пустой reserved stub с `__all__ = []`; он не содержит Alembic runtime wiring и не подключается конфигурацией.
- Создан `apps/api/migrations/versions/.gitkeep` для сохранения пустого каталога версий.
- `apps/edge/storage/schemas.py`, корневой `migrations/env.py` и `alembic.ini` не изменялись.

## Верификация / Тесты

- Baseline до правок: `.venv/bin/pytest apps/api/tests/api/test_health_stub.py -q --tb=line` → `1 passed`.
- После правок: `.venv/bin/pytest apps/api/tests/api/test_health_stub.py -q --tb=line` → `1 passed`.
- Ownership audit: корневой `alembic.ini` направляет `script_location` в `migrations`; корневой `migrations/env.py` импортирует `Base` из `apps.edge.storage.schemas`; API stub не содержит второго active Alembic chain.
- `.venv/bin/graphify update .` выполнен из корня репозитория.
- Pre-FINISH verify: targeted pytest green; публичный API, IPC wire, ORM schema и migration entrypoint сохранены; AC− и §0.11 проверены.

## Статус

`completed`
