# [v1-p1-pipeline-db-e2e | s08 | Docs matrix + pyproject markers (AC-PIPE-09, AC-PIPE-10)] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s08-docs-matrix-markers.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s08-docs-matrix-markers.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** infra (docs + config)  
**Статус:** completed

## Сделано

- `pyproject.toml`: добавлен маркер `e2e`:
  ```toml
  markers = [
      "integration: requires external broker or emulator",
      "slow: long-running soak or endurance test",
      "load: throughput and endurance harness",
      "e2e: end-to-end pipeline tests (compose or external dependencies)",
  ]
  ```

- `tests/conftest.py`: зарегистрирован маркер `e2e` через `pytest_configure`:
  ```python
  config.addinivalue_line("markers", "e2e: end-to-end pipeline tests (compose or external dependencies)")
  ```

- `apps/edge/collector/README.md`: добавлена секция **Pipeline DB E2E smoke (L2, AC-PIPE-07/08)**:
  - Команды запуска smoke: `scripts/smoke-pipeline-db.sh default|mqtt`
  - Exit codes (0/1/2) + TIMEOUT override
  - AC-PIPE-08: логирование TAI4101/TGEU4101 (не gate для exit)
  - Expected SQL примеры (COUNT, tag filter, sample peek)
  - **Layer matrix** (таблица): Layer | Tool | Маркер | Что доказывает | Команда
    - L0: pytest + testcontainers → IPC → samples/events
    - L1 MQTT: publisher → mosquitto → collector → writer → DB
    - L1 Modbus: emulator → connector → writer → DB
    - L2 compose: bash smoke default
    - L2 mqtt: bash smoke mqtt
    - Regression: storage + collector + emulator tests
  - pytest runner contract: `.venv/bin/pytest` из корня репо; `pythonpath` / `testpaths` из pyproject

- TDD: **нет** (docs + config; plan explicitly `tdd: no`).

- Anti-patterns / infra hygiene:
  - Маркер `e2e` — опционален; L0/L1 suite используют `integration` + `slow` (как было до s08).
  - Не добавлен mandatory marker gate в CI (не требуется планом).
  - Не трогает runtime code, writer entrypoint, compose topology.
  - Matrix документирует **существующее** доказательство (s01–s07), не создаёт новые claims.

- AC:
  - **AC-PIPE-09**: Документ матрицы доказательств в README fragment — **GREEN** (layer matrix + smoke команды + expected SQL).
  - **AC-PIPE-10**: Existing suites зелёные: `tests/storage/` + mqtt e2e + emulator mqtt tests — **PENDING** (regression в фоне; см. Верификация).

- code_changed: yes (pyproject.toml, tests/conftest.py, apps/edge/collector/README.md).

## Файлы

- `pyproject.toml` (edit: + `e2e` marker)
- `tests/conftest.py` (edit: + `e2e` в `pytest_configure`)
- `apps/edge/collector/README.md` (edit: + § Pipeline DB E2E smoke + matrix)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s08-docs-matrix-markers.md` (this)
- `memory-bank/activeContext.md` (Handoff + load_now)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s08-docs-matrix-markers.md` (reference)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/index.md` (status flip)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/index.md` (entry)

## Верификация

- Targeted (non-pytest):
  - `grep -A1 'e2e:' pyproject.toml` → маркер объявлен.
  - `grep 'e2e:' tests/conftest.py` → маркер зарегистрирован.
  - `grep -A30 'Pipeline DB E2E smoke' apps/edge/collector/README.md` → матрица + команды присутствуют.

- Регрессия (AC-PIPE-10):
  - Команда: `.venv/bin/pytest tests/storage apps/edge/collector/tests apps/edge/emulator/tests -q`
  - Статус: запущена в фоне (monitor task); результат см. ниже или в task output.
  - Ожидание: exit 0; 586 suite без новых fail (storage + collector + emulator).

- §0.11:
  - pyproject.toml: `testpaths` уже содержал `tests/pipeline` (из s03); добавлен только `markers`.
  - `tests/conftest.py`: добавлен маркер (уже регистрировал `integration`/`load`); `e2e` — consistent.
  - README: только docs, не runtime; все команды имеют counterpart в compose/scripts.
  - Не затронуты: `apps/edge/storage/writer.py`, `__main__.py`, entrypoint, Dockerfile, compose topology.
  - `docker-compose.yml` — без изменений.
  - compose/runtime entrypoint и публичный API writer — **не затронуты**.

- AC-PIPE-09: матрица в README (Layer | Tool | Маркер | Assert | Команда) — покрывает L0/L1/L2 + regression.
- AC-PIPE-10: см. регрессию (PENDING в момент записи; будет подтверждено parent после завершения).

- code_changed: yes (3 файла: pyproject, conftest, README).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.
- AC+: pyproject marker + conftest registration + README matrix + smoke команды; AC-PIPE-09 доказан docs.
- AC−: не ломать compose/runtime entrypoint и публичный API; не выходить за scope s08 (docs + markers, без фикса asset gaps / карт / collector-mqtt crash); regression не должен ввести новых fail.
- §0.11: все внешние ссылки (pytest markers, compose smoke, psql) имеют counterpart в pyproject/compose/scripts.
- VERIFY (parent): regression suite exit 0; targeted grep для маркера/матрицы.

## Статус

completed (FINISH: step-файл + ## Handoff в activeContext + decompose flip + load_now на QA; graphify после FINISH)
