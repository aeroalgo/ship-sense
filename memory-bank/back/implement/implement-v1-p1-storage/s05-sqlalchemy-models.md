# BACK IMPLEMENT s05 — SQLAlchemy models

## Результат
- Создан `apps/edge/storage/schemas.py` с SQLAlchemy 2 declarative-моделями для таблиц storage DDL.
- `migrations/env.py` использует `Base.metadata` и сохраняет `include_schemas=True`.
- Добавлены targeted model tests в `tests/storage/test_schemas.py`.
- Добавлены package markers `apps/__init__.py`, `apps/edge/__init__.py`, `apps/edge/storage/__init__.py`, `tests/storage/__init__.py` для корректного импорта из корня.

## Verification
- `PYTHONPATH=. .venv/bin/pytest tests/storage/test_schemas.py` — PASS (2 passed).
- `PYTHONPATH=. .venv/bin/python -c "from apps.edge.storage.schemas import Sample, Event; print('ok')"` — PASS.
- `PYTHONPATH=. .venv/bin/alembic check` — ожидаемо заблокирован: target database is not up to date; live DB не настроена.

## Handoff
Следующий шаг: BACK IMPLEMENT s06-samples-repo.
