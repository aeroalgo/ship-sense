# tasks.md — ShipSense

Индекс задач. Детальный статус шагов → `decompose-*/index.md`. Детали шага → `implement/sNN`. Навигация → `activeContext.md`. Хронология эпиков → `tasks/log/`.

## Активные

| ID | Title | Role | Plan | Step | Status |
|----|-------|------|------|------|--------|
| T-002 | storage + semantic | BACK | [plan](back/plan/plan-v1-p1-storage.md) · [dec](back/plan/decompose-v1-p1-storage/index.md) | s06 ✅ · CR-STO-04 ✅ | in_progress |
| T-001 | collector + emulator | BACK | [plan](back/plan/plan-v1-p1-collector.md) · [dec](back/plan/decompose-v1-p1-collector/index.md) · [gap](back/plan/plan-v1-p1-edge-runtime-smoke.md) | gap-close | in_progress |
| T-008 | MQTT connector | BACK | [plan](back/plan/plan-v1-p1-mqtt.md) · [dec](back/plan/decompose-v1-p1-mqtt/index.md) · [smoke](back/plan/plan-v1-p1-mqtt-smoke.md) | s12 ✅ · smoke BUGFIX ✅ · QA ✅ | next BACK REFLECT |

### Progress (компактно)

- **T-002** [dec](back/plan/decompose-v1-p1-storage/index.md): s01/s01b/s02/s03/s04/s05/s06 ✅ · CR-STO-04 ✅ · s07–s18 pending (s16 blocked CR-STO-01/02) → next IMPLEMENT s07
- **T-001** [dec](back/plan/decompose-v1-p1-collector/index.md): s01–s26 ✅ · gap-close smoke ⏳ ([plan](back/plan/plan-v1-p1-edge-runtime-smoke.md) — DECOMPOSE pending)
- **T-008** [dec](back/plan/decompose-v1-p1-mqtt/index.md): s01–s12 ✅ · smoke BUGFIX ✅ · QA ✅ → next BACK REFLECT

## Последние события

| Дата | Task | Событие |
|------|------|---------|
| 2026-07-29 | T-002 | BACK DECOMPOSE v1-p1-storage — index + s01–s18 |
| 2026-07-29 | T-002 | BACK IMPLEMENT v1-p1-storage s01b — TimescaleDB dev infra + live Alembic verification |
| 2026-07-29 | T-002 | BACK IMPLEMENT v1-p1-storage s04 — meta/health/quota/degrade Alembic migrations; offline verification PASS |
| 2026-07-29 | T-002 | BACK CREATIVE CR-STO-04 — frozen core + JSONB domain envelope; Q4=A/B validators; modes auto/native/reconstruct |
| 2026-07-29 | T-008 | BACK IMPLEMENT v1-p1-mqtt-smoke s07 — README §MQTT smoke commands + snippets |
| 2026-07-29 | T-008 | BACK BUGFIX mqtt-smoke ENTRYPOINT — single/dual/events PASS |
| 2026-07-29 | T-008 | BACK QA v1-p1-mqtt-smoke — PASS: all smoke modes and backend checks green |
| 2026-07-29 | T-008 | BACK IMPLEMENT v1-p1-mqtt-smoke s04 — dual-panel health smoke |
| 2026-07-28 | T-008 | BACK IMPLEMENT s11 — AC-MQTT-40 health mqtt fields |
| 2026-07-29 | T-008 | BACK PLAN mqtt-smoke — gap-close: publisher wire + compose E2E |
| 2026-07-28 | T-008 | BACK IMPLEMENT s09 R-1 — `aiomqtt.Topic` → str; E2E GREEN |
| 2026-07-28 | T-008 | BACK QA — dependencies resolved; s09 blocked by R-1 (`aiomqtt.Topic`) |

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
