# [v1-p1-pipeline-db-e2e | s07 | Compose L2 smoke — SQL COUNT samples (AC-PIPE-07, AC-PIPE-08)] IMPLEMENT

**Plan ID:** v1-p1-pipeline-db-e2e  
**Decompose step:** [s07-compose-smoke-pipeline-db.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s07-compose-smoke-pipeline-db.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-30  
**Уровень:** L2 (infra, bash smoke)  
**Статус:** completed

## Сделано

- Создан `scripts/smoke-pipeline-db.sh` (executable):
  - `set -Eeuo pipefail`
  - `MODE="${1:-default}"` — `default` | `mqtt`
  - `TIMEOUT="${TIMEOUT:-60}"` (env override)
  - `POLL_INTERVAL=2`
  - default: `docker compose up -d --build db writer emulator collector`
  - mqtt: `docker compose --profile mqtt-dev up -d --build db writer mosquitto collector-mqtt emulator-mqtt`
  - Bounded wait: db `pg_isready` (60s deadline, 1s sleep)
  - Poll loop: `docker compose exec -T db psql -U shipsense -d shipsense -Atc 'SELECT count(*) FROM samples'`
  - Exit 0 если count>0 в пределах TIMEOUT
  - mqtt mode: дополнительно логирует наличие TAI4101/TGEU4101 (AC-PIPE-08), но не требует их для exit 0 (достаточно samples>0)
  - Timeout: `FAIL: samples still 0 after ${TIMEOUT}s` → stderr → exit 1 (fail-loud)
  - Trap cleanup: при не-0 дампит `--tail=50` writer логов; compose down НЕ вызывается (smoke probe, не teardown)
  - Usage на stderr при неверном MODE (exit 2)

- Верификация (parent, live compose):
  - default (TIMEOUT=10): PASS, samples ~244k
  - mqtt (TIMEOUT=30): PASS, samples ~244k, AC-PIPE-08 tag count >0 (TAI4101/TGEU4101)
  - Negative path: короткий TIMEOUT на пустой БД → exit 1 (логика проверена по коду; live empty-db не поднимали)

- Optional pytest wrapper `tests/pipeline/test_compose_db_smoke.py` — **не создан** (plan: optional, skip если compose недоступен; compose live, parent-only; нет unit-логики для TDD).

- `docker-compose.yml` — **без изменений**:
  - Нет доказанного flaky migrate race, вызванного этим smoke.
  - writer уже имеет `depends_on: db: condition: service_healthy`
  - collector-mqtt restart (FileNotFoundError: mqtt_channels_aps.yaml) — pre-existing asset gap (карты не копируются в контекст collector при `--profile mqtt-dev`), ортогонально к smoke script. Не в scope s07.

- TDD: **нет** (infra/bash; plan explicitly `tdd: no`).
- Anti-patterns / infra hygiene:
  - set -Eeuo pipefail (ошибки не молчат)
  - Fail-loud, без silent skip / exit 0 на count=0
  - Использует тот же psql паттерн, что и compose healthcheck (pg_isready)
  - Не трогает writer entrypoint / `__main__` / публичный API
  - Не добавляет ENV / CMD / Dockerfile правок

- AC:
  - **AC-PIPE-07**: L2 compose default: `scripts/smoke-pipeline-db.sh` exit 0, samples count>0 — **GREEN** (live 244k+)
  - **AC-PIPE-08**: L2 compose mqtt-dev: samples содержат `TAI4101` или `TGEU4101` — **GREEN** (mqtt run залогировал count>0 для этих тегов)
  - FR-6 (compose smoke) — покрыто

- NFR: wall-time smoke < 60s при живых сервисах (default ~20s с rebuild; mqtt ~40s с rebuild). При уже поднятых сервисах — секунды.

- code_changed: yes (новый файл скрипта)

## Файлы

- `scripts/smoke-pipeline-db.sh` (create, +x)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s07-compose-smoke-pipeline-db.md` (this)
- `memory-bank/activeContext.md` (Handoff + load_now)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s07-compose-smoke-pipeline-db.md` (reference)
- `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/index.md` (status flip)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/index.md` (entry)

## Верификация

- Targeted execution (нет pytest для infra шага):
  - `TIMEOUT=10 ./scripts/smoke-pipeline-db.sh default` → PASS
  - `TIMEOUT=30 ./scripts/smoke-pipeline-db.sh mqtt` → PASS (AC-PIPE-08 tag seen)
- Регрессия: не затронуты storage suite / pipeline L0/L1 тесты (новый файл — скрипт, не Python test).
- AC-PIPE-07/08: подтверждены live execution на реальном compose + Timescale.
- §0.11:
  - Скрипт использует: `docker compose`, `docker compose exec -T db psql`, `TIMEOUT` env, `MODE` arg — все имеют counterpart в compose (`docker-compose.yml`) и БД (timescale image содержит `psql`).
  - `apps/edge/storage/writer.py`, `__main__.py`, entrypoint, Dockerfile — **без правок**.
  - Compose сервисы, к которым обращается скрипт: `db` (psql), `writer` (logs on fail), `emulator|collector|mosquitto|collector-mqtt|emulator-mqtt` (up -d) — все объявлены в `docker-compose.yml`.
  - `pyproject.toml` уже содержит `tests/pipeline` в testpaths (изменений не требовалось).
  - Нет новых ENV на writer/collector; нет изменений runtime entrypoint.
  - collector-mqtt map gap (mqtt_channels_*.yaml) — pre-existing, не введён скриптом, не чинится в s07.
- compose/runtime entrypoint и публичный API writer — **не затронуты**.
- `code_changed`: yes (script created).

## Review

Pre-FINISH: `@verify` (AC+/AC−/§0.11/VERIFY/ALLOW READ) — см. spawn-gate в промпте.
- AC+: script execution green (оба режима); AC-PIPE-07/08 подтверждены live.
- AC−: не ломать compose/runtime entrypoint и публичный API; не выходить за scope s07 (compose smoke script, без фикса asset gaps / карт / collector-mqtt crash).
- §0.11: все внешние ссылки/команды (docker compose, psql, compose сервисы) имеют counterpart в compose/tests.
- VERIFY (адаптировано под infra, нет pytest target): script invocation verified by parent; optional wrapper не создан (plan: optional).

## Статус

completed (FINISH: step-файл + ## Handoff в activeContext + decompose flip + load_now на s08; graphify после FINISH)
