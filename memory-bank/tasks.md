# tasks.md — ShipSense

Индекс задач. Детальный статус шагов → `decompose-*/index.md`. Детали шага → `implement/sNN`. Навигация → `activeContext.md`. Хронология эпиков → `tasks/log/`.

## Активные

| ID | Title | Role | Plan | Step | Status |
|----|-------|------|------|------|--------|
| T-002 | storage + semantic | BACK | [plan](back/plan/plan-v1-p1-storage.md) · [dec](back/plan/decompose-v1-p1-storage/index.md) · [pipeline-db-e2e](back/plan/plan-v1-p1-pipeline-db-e2e.md) · [dec-e2e](back/plan/decompose-v1-p1-pipeline-db-e2e/index.md) | s01–s18 ✅ · QA blocked→BUGFIX ✅ · pipeline-db-e2e s01 pending | next: BACK QA (re) → IMPLEMENT pipeline-db-e2e s01 |
| T-001 | collector + emulator | BACK | [plan](back/plan/plan-v1-p1-collector.md) · [dec](back/plan/decompose-v1-p1-collector/index.md) · [gap](back/plan/plan-v1-p1-edge-runtime-smoke.md) | gap-close | in_progress |
| T-008 | MQTT connector | BACK | [plan](back/plan/plan-v1-p1-mqtt.md) · [dec](back/plan/decompose-v1-p1-mqtt/index.md) · [smoke](back/plan/plan-v1-p1-mqtt-smoke.md) | s12 ✅ · smoke BUGFIX ✅ · QA ✅ | next BACK REFLECT |

### Progress (компактно)

- **T-002** [dec](back/plan/decompose-v1-p1-storage/index.md): s01–s18 ✅ · BUGFIX QA runtime ✅ · [pipeline-db-e2e](back/plan/decompose-v1-p1-pipeline-db-e2e/index.md) s01 ждёт после re-QA
- **T-001** [dec](back/plan/decompose-v1-p1-collector/index.md): s01–s26 ✅ · gap-close smoke ⏳ ([plan](back/plan/plan-v1-p1-edge-runtime-smoke.md) — DECOMPOSE pending)
- **T-008** [dec](back/plan/decompose-v1-p1-mqtt/index.md): s01–s12 ✅ · smoke BUGFIX ✅ · QA ✅ → next BACK REFLECT

## Последние события

| Дата | Task | Событие |
|------|------|---------|
| 2026-07-30 | T-002 | BACK IMPLEMENT pipeline-db-e2e s01 — WriterService.start_tcp + run_tcp refactor; 2 unit passed; AC-PIPE-06 | [implement](back/implement/implement-v1-p1-pipeline-db-e2e/s01-writer-start-tcp.md) |
| 2026-07-30 | T-002 | BACK BUGFIX QA runtime — ModbusException+runtime map, compression if_not_exists, mqtt broker timeout; full 400 passed | [bugfix](back/bugfix/bugfix-20260730-qa-storage-runtime.md) |
| 2026-07-30 | T-002 | BACK QA v1-p1-storage — BLOCKED: storage 65 / без slow 394; slow/full + runtime logs | [qa](back/qa/qa-20260730-v1-p1-storage.md) |
| 2026-07-29 | T-002 | BACK DECOMPOSE pipeline-db-e2e — s01–s08; CREATIVE нет; next IMPLEMENT s01 |
| 2026-07-29 | T-002 | BACK PLAN pipeline-db-e2e — emulator→collector→writer→Timescale SQL assert |
| 2026-07-29 | T-002 | BACK BUGFIX package-path + compose runtime |

→ полная лента: [`tasks/log/2026-07.md`](tasks/log/2026-07.md) (обновлять на FINISH)

## Backlog

| ID | Title | Role | Plan | Status |
|----|-------|------|------|--------|
| T-003 | API + session | BACK | [plan](back/plan/plan-v1-p1-api.md) | planned |
| T-004 | screens 1/5/8/6 | FRONT | [plan](front/plan/plan-v1-p1-screens.md) · [dec](front/plan/decompose-v1-p1-screens/index.md) | done |
| T-005 | ship backend v1 p2 | BACK | [plan](back/plan/plan-v1-p2-ship.md) | planned |
| T-006 | screens rest v1 p2 | FRONT | [plan](front/plan/plan-v1-p2-screens.md) | planned |
| T-007 | shore forward v2 | BACK | [plan](back/plan/plan-v2-shore.md) | planned |

## Delivery log

**Обязательно на FINISH** (atomic subtask): append строка в [`tasks/log/YYYY-MM.md`](tasks/log/2026-07.md) §Timeline + обновить §Последние события выше.  
Prose-архив: [`tasks/log/2026-07-legacy.md`](tasks/log/2026-07-legacy.md). **Не грузить** log на IMPLEMENT/TASK/QA.
