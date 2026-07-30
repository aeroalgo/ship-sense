# BACK REFACTOR — r03 move semantic

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r03`
- **Дата:** 2026-07-30
- **Behavior freeze:** SemanticEngine, SemanticPack, loader/quarantine public behavior, YAML schema and quarantine semantics.

## Реализация / Файлы

- Перенесён semantic-пакет из `apps/edge/semantic/` в `apps/api/app/semantic/`:
  - `__init__.py`
  - `models.py`
  - `loader.py`
  - `engine.py`
  - `quarantine.py`
- Все Python-импорты `apps.edge.semantic` заменены на `app.semantic` в storage entrypoints, storage consumers и semantic/storage tests.
- Старый каталог `apps/edge/semantic/` удалён; dual package и долгий shim не оставлены.
- `app.semantic.models` остаётся независимым от FastAPI imports.

## Верификация / Тесты

- Before baseline: `.venv/bin/pytest tests/storage/test_semantic_engine.py tests/storage/test_semantic_loader.py tests/storage/test_quarantine.py -q --tb=line` → `33 passed`.
- After refactor: та же targeted-команда → `33 passed`.
- Import smoke: `PYTHONPATH=apps/api .venv/bin/python -c 'import app.semantic, app.semantic.models, app.semantic.loader, app.semantic.engine, app.semantic.quarantine'` → PASS.
- Legacy import audit: `rg -n --glob '*.py' 'apps\\.edge\\.semantic' apps tests` → пусто.
- FastAPI ownership audit: в `apps/api/app/semantic` нет `fastapi` imports.
- Pre-FINISH verify: `VERDICT PASS`; AC+, AC−, §0.11 и все VERIFY-команды подтверждены.
- `.venv/bin/graphify update .` → PASS; graph rebuilt with 3125 nodes and 6528 edges.

## Статус

`completed`
