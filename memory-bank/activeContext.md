## load_now
1. [r05-amend-t003-plan-paths.md](memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/r05-amend-t003-plan-paths.md)
2. [plan-rf-fastapi-template-ownership.md](memory-bank/back/refactor/plan/plan-rf-fastapi-template-ownership.md) — AC E / amend T-003 paths
3. [index.md](memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) — очередь rNN

## Handoff BACK REFACTOR — r04

- **Предыдущий:** [session-20260730-r03-move-semantic.md](memory-bank/back/refactor/session-20260730-r03-move-semantic.md) — r03 completed
- **Следующий:** `BACK REFACTOR` @r05 — [r05-amend-t003-plan-paths.md](memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/r05-amend-t003-plan-paths.md)
- **Сделано:** 
  - Создан усиленный `apps/api/tests/unit/test_domain_no_fastapi.py`: AST-проверка — `app.telemetry`/`app.events`/`app.semantic` не импортируют `fastapi`/`starlette`/`app.api`/`app.main`.
  - Создан `apps/edge/collector/tests/unit/test_plugins_no_app_canonical.py`: транспортные плагины (кроме mapping) не импортируют `app.telemetry`/`app.events` (только Raw* + health).
  - Подтверждён `tests/storage/test_no_collector_domain_canonical.py`: storage не импортирует `collector.domain` canonical.
  - Обновлён `apps/edge/collector/README.md`: добавлена секция **Ownership** с явными правилами и ссылками на три regression-теста (plan §5.6 Фаза F).
- **Верификация:** 
  - Before baseline: `2 passed`.
  - After targeted (3 файла): `PYTHONPATH=apps/edge/collector/src:apps/api:. .venv/bin/pytest ... -q --override-ini="addopts="` → `3 passed`.
  - Pre-FINISH verify (Agent subagent_type=verify): VERDICT PASS (AC+, AC−, §0.11, VERIFY команда).
  - Smoke unit: collector unit + storage unit (pipeline DB integration errors не в scope r04).
- **code_changed:** yes
- **New chat:** yes → `BACK REFACTOR` @r05

## done — do NOT load
- `memory-bank/back/refactor/session-20260730-r04-import-graph-audit.md`
- `memory-bank/back/refactor/implement/implement-rf-fastapi-template-ownership/r04-import-graph-audit.md`
- `memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/r04-import-graph-audit.md`
- `memory-bank/back/refactor/session-20260730-r03-move-semantic.md`
- `memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/r03-move-semantic.md`
- `memory-bank/back/refactor/implement/implement-rf-fastapi-template-ownership/r02-move-canonical-models.md`
- `memory-bank/back/refactor/session-20260730-r01-scaffold-apps-api.md`