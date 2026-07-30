# T-002 / v1-p1-storage QA

**Дата:** 2026-07-29  
**Reviewer:** BACK QA  
**Verdict:** blocked

## Scope

- task: T-002
- step: s01–s18 storage + semantic, с фокусом на s17/s18 integration wiring и storage tests
- files: `apps/edge/storage/`, `apps/edge/semantic/`, `migrations/versions/`, `docker-compose.yml`, `tests/storage/`, `pyproject.toml`

## Checks

- [x] storage suite green: `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/ -q` — 63 passed
- [x] storage + collector unit tests green: `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest apps/edge/collector/tests/unit tests/storage -q` — 63 passed
- [x] Python syntax: `python3 -m compileall -q apps tests` — pass
- [x] compose syntax: `docker compose config -q` — pass
- [x] storage integration refs inspected (§0.11): compose, writer exports, database dependency and test wiring are internally consistent
- [x] storage edge cases covered by existing contract, correlation, quota, quarantine and load tests
- [ ] full repository suite green
- [ ] live compose storage stack verified
- [ ] lint command available and green

## Issues

| ID | sev | file | msg |
|----|-----|------|-----|
| QA-1 | blocker | `apps/edge/collector/tests/conftest.py:26` | Полный suite не стартует: `ModuleNotFoundError: No module named 'collector'` при collection без `PYTHONPATH=.:apps/edge/collector/src`. Конфигурация `pyproject.toml` не содержит `pythonpath`, а QA-команда из канона запускается без package path. |
| QA-2 | blocker | `apps/edge/emulator/tests/*` | Emulator tests не стартуют с текущим package layout: `ModuleNotFoundError: No module named 'emulator'`. Попытки с `PYTHONPATH=.:apps/edge/emulator/src` и `PYTHONPATH=.:apps/edge/emulator` не устранили import error; требуется отдельный runtime/package-path fix. |
| QA-3 | high | `docker-compose.yml` / рабочий compose state | `docker compose ps` показывает запущенный `shipsense-writer` на старом образе `shipsense/writer-stub:dev`, тогда как s17 ожидает `shipsense/writer:dev`, и `shipsense-collector` находится в `Restarting (1)`. Live compose acceptance не подтверждён. |
| QA-4 | medium | `.venv` | `.venv/bin/ruff` отсутствует, поэтому lint gate не выполнен этим инструментом. |
| QA-5 | low | `.cursor/rules/back_developer/isolation_rules/_lean/creative.mdc`, `.kilo/instructions/spawn-hard.md` | `git diff --check` сообщает trailing whitespace в изменениях workflow-инструкций; не относится к storage runtime, но рабочее дерево не проходит whitespace check. |

## Blockers

- Нельзя объявить BACK QA PASS до исправления package-path/collection blockers QA-1 и QA-2 либо явного CI runner contract, который стабильно запускает весь suite.
- Нельзя считать s17 live acceptance подтверждённым до пересоздания compose writer из текущего storage image и устранения restart loop collector.

## Recommended next action

`BACK BUGFIX` для package-path collection и compose runtime state, затем повторить BACK QA. Storage targeted suite отдельно проходит: 63/63.
