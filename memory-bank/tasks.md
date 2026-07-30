# tasks.md — ShipSense

Индекс задач. Детальный статус шагов → `decompose-*/index.md`. Детали шага → `implement/sNN`. Навигация → `activeContext.md`. Хронология эпиков → `tasks/log/`.

## Активные

| ID | Title | Role | Plan | Step | Status |
|----|-------|------|------|------|--------|
| RF-01 | fastapi-template ownership | BACK | [plan](back/refactor/plan/plan-rf-fastapi-template-ownership.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) | r04 import-graph audit | REFACTOR r04 done · next REFACTOR @r05 |
| T-003 | API + session (B10/B11) | BACK | [plan](back/plan/plan-v1-p1-api.md) · [dec](back/plan/decompose-v1-p1-api/index.md) | s01 scaffold | **blocked** until RF-01 r01+r02+r05 |

### Progress (компактно)

- RF-01: DECOMPOSE r01–r06; r01 scaffold + r02 canonical models + r03 semantic done; next `BACK REFACTOR` @r04 import-graph audit
- T-003: IMPLEMENT s01 blocked until RF-01 r01+r02+r05

## Архив эпиков

| ID | Title | Role | Paths | Status |
|----|-------|------|-------|--------|
| T-001 | collector + emulator | BACK | [plan](archive/back/plan/plan-v1-p1-collector.md) · [dec](archive/back/plan/decompose-v1-p1-collector/index.md) · [impl](archive/back/implement/implement-v1-p1-collector/index.md) · [qa](archive/back/qa/v1-p1-collector/) · [reflection](back/reflection/reflection-T-001-v1-p1-collector.md) · gap live: [edge-runtime-smoke](back/plan/plan-v1-p1-edge-runtime-smoke.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-002 | storage + semantic | BACK | [plan](archive/back/plan/plan-v1-p1-storage.md) · [dec](archive/back/plan/decompose-v1-p1-storage/index.md) · [impl](archive/back/implement/implement-v1-p1-storage/index.md) · [qa](archive/back/qa/v1-p1-storage/) · [creative](archive/back/creative/v1-p1-storage/) · [reflection](back/reflection/reflection-T-002-v1-p1-storage.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-002 / pipeline-db-e2e | pipeline → Timescale e2e | BACK | [plan](archive/back/plan/plan-v1-p1-pipeline-db-e2e.md) · [dec](archive/back/plan/decompose-v1-p1-pipeline-db-e2e/index.md) · [impl](archive/back/implement/implement-v1-p1-pipeline-db-e2e/index.md) · [qa](archive/back/qa/v1-p1-pipeline-db-e2e/) · [reflection](back/reflection/reflection-T-002-v1-p1-pipeline-db-e2e.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-008 | MQTT connector | BACK | [plan](archive/back/plan/plan-v1-p1-mqtt.md) · [dec](archive/back/plan/decompose-v1-p1-mqtt/index.md) · [impl](archive/back/implement/implement-v1-p1-mqtt/index.md) · [smoke](archive/back/plan/plan-v1-p1-mqtt-smoke.md) · [qa](archive/back/qa/v1-p1-mqtt/) · [reflection](back/reflection/reflection-T-008-v1-p1-mqtt.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |

## Последние события

| Дата | Task | Событие |
|------|------|---------|
| 2026-07-30 | RF-01 | BACK REFACTOR r01 — scaffold `apps/api`, health stub, pythonpath/testpaths; next REFACTOR @r02 | [session](back/refactor/session-20260730-r01-scaffold-apps-api.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r02 — canonical Quality/TelemetrySample/Event* перенесены в `apps/api/app`, collector domain разделён на Raw*/health, storage/tests rewired; targeted pytest PASS (373 passed). Следующий шаг: r03 | [session](back/refactor/implement/implement-rf-fastapi-template-ownership/r02-move-canonical-models.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r04 — import-graph audit tests + README ownership; three regression tests green; pre-FINISH verify PASS; next REFACTOR @r05 | [session](back/refactor/session-20260730-r04-import-graph-audit.md) · [r04](back/refactor/implement/implement-rf-fastapi-template-ownership/r04-import-graph-audit.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r03 — semantic перенесён в `apps/api/app/semantic`, импорты rewired, старый пакет удалён; targeted pytest PASS (33 passed), import smoke PASS. Следующий шаг: r04 | [session](back/refactor/session-20260730-r03-move-semantic.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR PLAN rf-fastapi-template-ownership — skill layout `apps/api`; next DECOMPOSE | [plan](back/refactor/plan/plan-rf-fastapi-template-ownership.md) |
| 2026-07-30 | T-003 | BACK DECOMPOSE v1-p1-api — index + s01–s10; CREATIVE CR-API-01..05 open; IMPLEMENT blocked by RF-01 | [dec](back/plan/decompose-v1-p1-api/index.md) |
| 2026-07-30 | T-002 | BACK ARCHIVE NOW v1-p1-storage — plan/decompose/implement/creative/qa/bugfix → archive/back/; ЗАВЕРШЕНА И АРХИВИРОВАНА | [impl](archive/back/implement/implement-v1-p1-storage/index.md) |
| 2026-07-30 | T-002 | BACK REFLECT v1-p1-storage — L4 s01–s18; re-QA PASS / BUGFIX cycles; next BACK ARCHIVE NOW | [reflection](back/reflection/reflection-T-002-v1-p1-storage.md) |
| 2026-07-30 | T-008 | BACK ARCHIVE NOW v1-p1-mqtt (+ mqtt-smoke) — дерево в archive/back/; reflection на месте; ЗАВЕРШЕНА И АРХИВИРОВАНА | [impl](archive/back/implement/implement-v1-p1-mqtt/index.md) |
| 2026-07-30 | T-008 | BACK REFLECT v1-p1-mqtt — L4 s01–s12 + smoke; Topic/ENTRYPOINT lessons; next BACK ARCHIVE NOW | [reflection](back/reflection/reflection-T-008-v1-p1-mqtt.md) |
| 2026-07-30 | T-002 | BACK ARCHIVE NOW v1-p1-pipeline-db-e2e — plan/decompose/implement/qa → archive/back/; reflection на месте | [impl](archive/back/implement/implement-v1-p1-pipeline-db-e2e/index.md) |

→ полная лента: [`tasks/log/2026-07.md`](tasks/log/2026-07.md) (обновлять на FINISH)

## Backlog

| ID | Title | Role | Plan | Status |
|----|-------|------|------|--------|
| T-003 | API + session | BACK | [plan](back/plan/plan-v1-p1-api.md) · [dec](back/plan/decompose-v1-p1-api/index.md) | **активна, blocked RF-01** — см. §Активные |
| T-004 | screens 1/5/8/6 | FRONT | [plan](front/plan/plan-v1-p1-screens.md) · [dec](front/plan/decompose-v1-p1-screens/index.md) | done |
| T-005 | ship backend v1 p2 | BACK | [plan](back/plan/plan-v1-p2-ship.md) | planned |
| T-006 | screens rest v1 p2 | FRONT | [plan](front/plan/plan-v1-p2-screens.md) | planned |
| T-007 | shore forward v2 | BACK | [plan](back/plan/plan-v2-shore.md) | planned |

## Delivery log

**Обязательно на FINISH** (atomic subtask): append строка в [`tasks/log/YYYY-MM.md`](tasks/log/2026-07.md) §Timeline + обновить §Последние события выше.  
Prose-архив: [`tasks/log/2026-07-legacy.md`](tasks/log/2026-07-legacy.md). **Не грузить** log на IMPLEMENT/TASK/QA.
