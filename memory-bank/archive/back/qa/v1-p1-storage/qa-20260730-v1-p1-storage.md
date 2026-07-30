# T-002 / v1-p1-storage QA

**Дата:** 2026-07-30  
**Reviewer:** BACK QA  
**Verdict:** blocked

## Scope

- task: T-002
- step: s01–s18 storage + semantic, с фокусом на s17/s18 integration wiring и storage tests
- files: `apps/edge/storage/`, `apps/edge/semantic/`, `migrations/versions/`, `docker-compose.yml`, `tests/storage/`, `pyproject.toml`

## Checks

- [x] storage suite green: `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/ -q` — **65 passed in 0.58s**
- [x] backend suite без slow-тестов: `.venv/bin/pytest -m 'not slow' -q` — **394 passed, 3 deselected, 1 warning in 16.87s**
- [x] full suite collection: `.venv/bin/pytest --collect-only -q` — **397 tests collected**
- [x] Python syntax: `.venv/bin/python -m compileall -q apps/edge tests/storage` — pass
- [x] compose syntax: `docker compose config --quiet` — pass
- [x] live Compose state: `docker compose ps` — `db`, `writer`, `collector`, `emulator` healthy; writer image `shipsense/writer:dev`
- [x] live DB storage presence: `docker compose exec -T db psql ... '\dt'` — `samples`, `events`, semantic/quarantine/quota/health tables present
- [x] live DB data sanity: `samples=75352`, `events=1929`, Alembic `006_compression_retention`
- [x] storage integration refs inspected (§0.11): compose, writer exports, database dependency and test wiring are internally consistent
- [x] storage edge cases covered by contract, correlation, quota, quarantine and load tests
- [ ] full repository suite including slow tests green
- [ ] lint/types/security tools green: `ruff`, `mypy`, `semgrep`, `bandit` unavailable in `.venv`

## Issues

| ID | sev | file | msg |
|----|-----|------|-----|
| QA-1 | blocker | `apps/edge/collector/tests/integration/test_mqtt_e2e.py` | Slow/full suite did not reach a terminal result within the 180-second QA budget; execution stopped while running `test_mosquitto_mqtt_collector_emits_sample_and_lifecycle_event`. Поэтому полный suite не объявляется green. |
| QA-2 | high | `docker-compose.yml` / live logs | Live services healthy, но `docker compose logs` содержит повторяющиеся `ModbusException` для poll groups и DB warnings/errors: compression policy already exists и запрос отсутствующей `timescaledb_information.jobs.last_run_started_at`. Live storage acceptance частично подтверждена counts/health, но runtime logs не чистые. |
| QA-3 | medium | `.venv` | `ruff`, `mypy`, `semgrep`, `bandit` отсутствуют; lint/type/security gates этим инструментарием не выполнены. |
| QA-4 | low | `.cursor/rules/back_developer/isolation_rules/_lean/creative.mdc`, `.kilo/instructions/spawn-hard.md` | `git diff --check` в рабочем дереве сообщает trailing whitespace в изменениях workflow-инструкций; это не storage runtime regression. |

## Blockers

- Нельзя объявить BACK QA PASS, пока slow/full pytest suite не получает terminal green result либо не введён явный CI/runtime contract с отдельным smoke acceptance.
- Live Compose writer/DB/collector подняты и данные записываются, но повторяющиеся runtime errors/warnings требуют отдельного расследования до безусловного acceptance.
- Статические lint/type/security gates остаются непроверенными из-за отсутствующих инструментов.

## Reviewer result

- `reviewer` выполнен после suite с packed AC+/AC−/§0.11/ALLOW.
- AC+ storage contracts, storage suite, testpaths/marker, syntax и compose config — подтверждены.
- AC− соблюдены: mocks не считались live DB acceptance; полный suite не объявлен green; недоступные инструменты явно указаны; unrelated docs whitespace не выдан за storage regression.
- §0.11: compose env/IPC (`DATABASE_URL`, `SHIPSSENSE_WRITER_ENDPOINT`, port `9009`) согласованы; live DB tables/counts подтверждены.
- Reviewer verdict был PASS для проверенного storage scope, но общий QA verdict остаётся **blocked** из-за незавершённого slow/full suite и runtime log errors.

## Next

`BACK BUGFIX` для slow/full-suite runtime и повторяющихся compose log errors, затем повторить `BACK QA`.
