# tasks.md — ShipSense

Индекс задач. Детальный статус шагов → `decompose-*/index.md`. Детали шага → `implement/sNN`. Навигация → `activeContext.md`. Хронология эпиков → `tasks/log/`.

## Активные

| ID | Title | Role | Plan | Step | Status |
|----|-------|------|------|------|--------|
| T-006 | portal wire BACK↔FRONT | INTEG | [plan](integration/plan/plan-v1-portal.md) | e01–e05 completed; next e06 | **IMPLEMENT active** · next `INTEG IMPLEMENT` e06 |
| T-005 | ship backend v1 p2 | BACK | [plan](back/plan/plan-v1-p2-ship.md) · [dec](back/plan/decompose-v1-p2-ship/index.md) · [impl](back/implement/implement-v1-p2-ship/index.md) · [qa](back/qa/v1-p2-ship/qa-20260801-v1-p2-ship.md) · [reflection](back/reflection/reflection-T-005-v1-p2-ship.md) | s01–s20 completed; CR-P2-01/02/03/04/05/06/07/08/09/10/11/12 closed | **BACK REFLECT complete** · next `BACK ARCHIVE NOW` |
| T-003 | API + session (B10/B11) | BACK | [plan](back/plan/plan-v1-p1-api.md) · [dec](back/plan/decompose-v1-p1-api/index.md) · [impl](back/implement/implement-v1-p1-api/index.md) · [qa](back/qa/v1-p1-api/qa-20260731-v1-p1-api.md) · [reflection](back/reflection/reflection-T-003-v1-p1-api.md) | s01–s10 done | **REFLECT complete** · next `BACK ARCHIVE NOW` |
| RF-01 | fastapi-template ownership | BACK | [plan](back/refactor/plan/plan-rf-fastapi-template-ownership.md) · [dec](back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md) · [qa](back/qa/rf-fastapi-template-ownership/qa-20260730-rf-fastapi-template-ownership.md) | r06 done | QA PASS · REFLECT отложен (после T-003 / отдельно) |

### Progress (компактно)

- T-006: INTEG e05 completed; StatusBar alarm/warning bootstrap, journal deep-link and live WS wire verified; targeted frontend checks passed, verify PASS; next e06 in a new INTEG IMPLEMENT chat
- T-006: INTEG e03 completed; session create/logout wire verified; targeted frontend/backend checks passed; next e04 in a new INTEG IMPLEMENT chat
- T-005: s01–s20 completed; QA PASS; REFLECT complete; next BACK ARCHIVE NOW
- T-003: s01–s10 done; CR-API-01..05 creative closed; QA PASS and REFLECT complete; next BACK ARCHIVE NOW
- RF-01: r01–r06 + QA PASS; REFLECT deferred

## Архив эпиков

| ID | Title | Role | Paths | Status |
|----|-------|------|-------|--------|
| T-001 | collector + emulator | BACK | [plan](archive/back/plan/plan-v1-p1-collector.md) · [dec](archive/back/plan/decompose-v1-p1-collector/index.md) · [impl](archive/back/implement/implement-v1-p1-collector/index.md) · [qa](archive/back/qa/v1-p1-collector/) · [reflection](back/reflection/reflection-T-001-v1-p1-collector.md) · gap live: [edge-runtime-smoke](back/plan/plan-v1-p1-edge-runtime-smoke.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-002 | storage + semantic | BACK | [plan](archive/back/plan/plan-v1-p1-storage.md) · [dec](archive/back/plan/decompose-v1-p1-storage/index.md) · [impl](archive/back/implement/implement-v1-p1-storage/index.md) · [qa](archive/back/qa/v1-p1-storage/) · [creative](archive/back/creative/v1-p1-storage/) · [reflection](back/reflection/reflection-T-002-v1-p1-storage.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-002 / pipeline-db-e2e | pipeline → Timescale e2e | BACK | [plan](archive/back/plan/plan-v1-p1-pipeline-db-e2e.md) · [dec](archive/back/plan/decompose-v1-p1-pipeline-db-e2e/index.md) · [impl](archive/back/implement/implement-v1-p1-pipeline-db-e2e/index.md) · [qa](archive/back/qa/v1-p1-pipeline-db-e2e/) · [reflection](back/reflection/reflection-T-002-v1-p1-pipeline-db-e2e.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |
| T-008 | MQTT connector | BACK | [plan](archive/back/plan/plan-v1-p1-mqtt.md) · [dec](archive/back/plan/decompose-v1-p1-mqtt/index.md) · [impl](archive/back/implement/implement-v1-p1-mqtt/index.md) · [smoke](archive/back/plan/plan-v1-p1-mqtt-smoke.md) · [qa](archive/back/qa/v1-p1-mqtt/) · [reflection](back/reflection/reflection-T-008-v1-p1-mqtt.md) | **ЗАВЕРШЕНА И АРХИВИРОВАНА** |

## Последние события
| 2026-08-01 | T-006 | INTEG IMPLEMENT e03 completed: session create/logout wire verified; integ-step format PASS; next `INTEG IMPLEMENT` e04 | [e03](integration/implement/implement-v1-portal/e03-session-create-logout.md) · [e04](integration/plan/decompose-v1-portal/e04-appshell-chrome.md) |
| 2026-08-01 | T-006 | INTEG PLAN v1-portal completed: registry e01–e30, API inventory, journeys; next `INTEG DECOMPOSE` | [plan](integration/plan/plan-v1-portal.md) |
| 2026-08-01 | T-005 | BACK IMPLEMENT s19 completed: I4 integration/acceptance runbooks + training; docs-only; FINISH AC/ledger restored after idle-timeout; next `BACK CREATIVE` CR-P2-11 | [s19](back/implement/implement-v1-p2-ship/s19-i4-runbook.md) · [s20](back/plan/decompose-v1-p2-ship/s20-integration-hard.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-06 completed: explicit roster roles, deny-by-default permission matrix, session role snapshot and fail-closed admin authorization; dependents rewired; next `BACK IMPLEMENT` @s14 | [creative](back/creative/v1-p2-ship/creative-b11-roles.md) · [s14](back/plan/decompose-v1-p2-ship/s14-i7-hardening-audit.md) · [s16](back/plan/decompose-v1-p2-ship/s16-admin-api-storage-ota.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-10/12 completed: typed fail-closed OTA health policy, anchorage gate, Ubuntu 24.04 LTS minimal + RAUC/U-Boot A/B contract; dependents rewired; next `BACK IMPLEMENT` @s12 | [creative](back/creative/v1-p2-ship/creative-ota-edge.md) · [s12](back/plan/decompose-v1-p2-ship/s12-i5-ota-rauc.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-03 completed: ZFS mirror, atomic daily events/config backup, disposable restore verification, typed storage health and inclusive 80% alert; dependents rewired; next `BACK IMPLEMENT` @s13 | [creative](back/creative/v1-p2-ship/creative-raid-storage.md) · [s13](back/plan/decompose-v1-p2-ship/s13-i6-raid-backup.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-05 completed: typed mnemo YAML contract, immutable registry, pure sibling_mean_delta, quarantine→unknown/null and schema-aware REST/WS seam; dependents rewired; next `BACK IMPLEMENT` @s08 | [creative](back/creative/v1-p2-ship/creative-mnemo-computed.md) · [s08](back/plan/decompose-v1-p2-ship/s08-mnemo-bindings-loader.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-08 completed: explicit 53-tag B13 baseline, APS-first setpoints, SKT001 mode filter, continuous-time EWMA/trend/ETA and fail-closed validation; next `BACK IMPLEMENT` @s06 | [creative](back/creative/v1-p2-ship/creative-b13-tag-set.md) · [s06](back/plan/decompose-v1-p2-ship/s06-b13-drift-engine.md) |
| 2026-07-31 | T-005 | BACK IMPLEMENT s03 completed: versioned B12 formulas ship-pack, FormulaLoader, motohours/fuel/time-weighted integrators, quality gaps and presentation rounding; targeted formulas 7 passed; next `BACK CREATIVE` CR-P2-07 for s04 | [s03](back/implement/implement-v1-p2-ship/s03-b12-formulas-v1.md) · [s04](back/plan/decompose-v1-p2-ship/s04-b12-templates.md) |
| 2026-07-31 | T-005 | BACK IMPLEMENT s04 completed: TemplateRenderer with shared JSON/HTML context, watch alarm debounce, provenance partial, register waiver validation, versioned report templates; targeted reports/API tests 8 passed; next `BACK IMPLEMENT` @s05 | [s04](back/implement/implement-v1-p2-ship/s04-b12-templates.md) · [s05](back/plan/decompose-v1-p2-ship/s05-b12-t9-fixtures.md) |
| 2026-07-31 | T-005 | BACK CREATIVE CR-P2-07 completed: TemplateRenderer context contract, deterministic anchor-window alarm debounce, common provenance frame and Q5 waiver-first register decision; next `BACK IMPLEMENT` @s04 | [creative](back/creative/v1-p2-ship/creative-report-forms.md) · [s04](back/plan/decompose-v1-p2-ship/s04-b12-templates.md) |
| 2026-07-31 | T-005 | BACK CREATIVE v1-p2-ship — CR-P2-01/02/04 closed; gateway, RAUC A/B and B12 formula contracts fixed; next `BACK IMPLEMENT` @s01 | [creative](back/creative/v1-p2-ship/creative-i1-ota-b12.md) · [dec](back/plan/decompose-v1-p2-ship/index.md) |
| 2026-07-31 | T-005 | BACK IMPLEMENT s01 completed: I1 read-only Modbus gateway, reject logging, fragmented/pipelined MBAP parser and collector→gateway→emulator compose isolation; targeted gateway tests 11 passed; next `BACK IMPLEMENT` @s02 | [s01](back/implement/implement-v1-p2-ship/s01-i1-gateway.md) · [s02](back/plan/decompose-v1-p2-ship/s02-b12-engine-core.md) |
| 2026-07-31 | T-003 | BACK REFLECT v1-p1-api completed: plan/decompose vs fact, lessons and process improvements recorded; AC− slow/full и live compose smoke preserved; next `BACK ARCHIVE NOW` | [reflection](back/reflection/reflection-T-003-v1-p1-api.md) · [qa](back/qa/v1-p1-api/qa-20260731-v1-p1-api.md) |
| 2026-07-31 | T-003 | BACK QA v1-p1-api PASS: storage 82 passed; backend без slow 453 passed, 9 deselected, 3 warnings; reviewer PASS; slow/full и live compose smoke вне scope; next `BACK REFLECT` | [qa](back/qa/v1-p1-api/qa-20260731-v1-p1-api.md) · [plan](back/plan/plan-v1-p1-api.md) |
| 2026-07-31 | T-003 | BACK IMPLEMENT s10 completed: I1 static import denylist, OpenAPI REST surface/mutation audit, quarantine example and README disclaimer; targeted tests 5 passed, API tests 39 passed (2 warnings); next `BACK QA` v1-p1-api | [s10](back/implement/implement-v1-p1-api/s10-tests-i1-openapi.md) · [qa](back/implement/implement-v1-p1-api/index.md) |

| Дата | Task | Событие |
|------|------|---------|
| 2026-07-31 | T-003 | BACK IMPLEMENT s08 completed: reports catalog + watch JSON/HTML, deterministic verdict/highlights/KPI/data-quality; targeted reports tests 3 passed; next `BACK IMPLEMENT` @s09 | [s08](back/implement/implement-v1-p1-api/s08-reports-watch.md) · [s09](back/plan/decompose-v1-p1-api/s09-health-sources-rate.md) |
| 2026-07-30 | T-003 | BACK IMPLEMENT s07 completed: roster + POST/DELETE session, HttpOnly cookie, idle/max TTL, supersede and B6 audit events; targeted session tests 3 passed; next `BACK IMPLEMENT` @s08 | [s07](back/implement/implement-v1-p1-api/s07-session-b11.md) · [s08](back/plan/decompose-v1-p1-api/s08-reports-watch.md) |
| 2026-07-30 | T-003 | BACK IMPLEMENT s05 completed: read-only `/api/setpoints` + `/api/setpoints/history` from YAML, schemas/service/router/fixture; targeted setpoints tests 4 passed; next `BACK IMPLEMENT` @s06 | [s05](back/implement/implement-v1-p1-api/s05-setpoints.md) · [s06](back/plan/decompose-v1-p1-api/s06-ws-fanout.md) |
| 2026-07-30 | T-003 | BACK IMPLEMENT s04 completed: `GET /api/events`, opaque cursor, keyset query, filters, response schemas; targeted events/repository 7 passed; next `BACK IMPLEMENT` @s05 | [s04](back/implement/implement-v1-p1-api/s04-events-rest.md) · [s05](back/plan/decompose-v1-p1-api/s05-setpoints.md) |
| 2026-07-30 | T-003 | BACK IMPLEMENT s03 completed: `/api/series` + aggregate, DownsampleService, auto resolution, worst-of quality, gap omission, bool last; targeted s03 11 passed, API regression 15 passed; next `BACK IMPLEMENT` @s04 | [s03](back/implement/implement-v1-p1-api/s03-series-downsample.md) · [s04](back/plan/decompose-v1-p1-api/s04-events-rest.md) |
| 2026-07-30 | T-003 | BACK IMPLEMENT s02 completed: `/api/assets/tree`, aggregate status, cache, 503 semantic guard; targeted API tests 3 passed, API tests 5 passed; next `BACK CREATIVE` CR-API-01..05 | [s02](back/implement/implement-v1-p1-api/s02-assets-tree.md) · [s03](back/plan/decompose-v1-p1-api/s03-series-downsample.md) |
| 2026-07-30 | T-003 | BACK CREATIVE CR-API-01..05 completed in one batch; downsample, WS fanout, session lifecycle, cursor and report-stub contracts fixed; dependents rewired; next `BACK IMPLEMENT` @s03 | [creative-api-gates.md](back/creative/v1-p1-api/creative-api-gates.md) · [dec](back/plan/decompose-v1-p1-api/index.md) · [s03](back/plan/decompose-v1-p1-api/s03-series-downsample.md) |
| 2026-07-30 | T-003 | Handoff: resume v1-p1-api; next `BACK IMPLEMENT` @s01 (RF-01 REFLECT deferred) | [dec](back/plan/decompose-v1-p1-api/index.md) · [s01](back/plan/decompose-v1-p1-api/s01-scaffold.md) |
| 2026-07-30 | RF-01 | BACK QA rf-fastapi-template-ownership — PASS; storage 77 passed; backend без slow 410 passed, 9 deselected; reviewer PASS; slow/full и live compose вне scope | [qa](back/qa/rf-fastapi-template-ownership/qa-20260730-rf-fastapi-template-ownership.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r05 — T-003 plan/decompose paths verified on `apps/api`; docs-only; next r06 | [session](back/refactor/session-20260730-r05-amend-t003-plan-paths.md) · [r05](back/refactor/implement/implement-rf-fastapi-template-ownership/r05-amend-t003-plan-paths.md) |
| 2026-07-30 | T-003 | BACK DECOMPOSE v1-p1-api — index + s01–s10 (`apps/api`); CREATIVE open; next CREATIVE или IMPLEMENT s01 | [dec](back/plan/decompose-v1-p1-api/index.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r04 — import-graph audit tests + README ownership; three regression tests green; next REFACTOR @r05 | [session](back/refactor/session-20260730-r04-import-graph-audit.md) · [r04](back/refactor/implement/implement-rf-fastapi-template-ownership/r04-import-graph-audit.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r03 — semantic → `apps/api/app/semantic`; next r04 | [session](back/refactor/session-20260730-r03-move-semantic.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r02 — canonical models → `apps/api/app`; next r03 | [r02](back/refactor/implement/implement-rf-fastapi-template-ownership/r02-move-canonical-models.md) |
| 2026-07-30 | RF-01 | BACK REFACTOR r01 — scaffold `apps/api`, health stub; next r02 | [session](back/refactor/session-20260730-r01-scaffold-apps-api.md) |

→ полная лента: [`tasks/log/2026-07.md`](tasks/log/2026-07.md) (обновлять на FINISH)

## Backlog

| ID | Title | Role | Plan | Status |
|----|-------|------|------|--------|
| T-003 | API + session | BACK | [plan](back/plan/plan-v1-p1-api.md) · [dec](back/plan/decompose-v1-p1-api/index.md) | **активна** — DECOMPOSE done; см. §Активные |
| T-004 | screens 1/5/8/6 | FRONT | [plan](front/plan/plan-v1-p1-screens.md) · [dec](front/plan/decompose-v1-p1-screens/index.md) | done |
| T-005 | ship backend v1 p2 | BACK | [plan](back/plan/plan-v1-p2-ship.md) · [dec](back/plan/decompose-v1-p2-ship/index.md) | **активна** — DECOMPOSE done; см. §Активные |
| T-006 | screens rest v1 p2 | FRONT | [plan](front/plan/plan-v1-p2-screens.md) | planned |
| T-007 | shore forward v2 | BACK | [plan](back/plan/plan-v2-shore.md) | planned |

## Delivery log

**Обязательно на FINISH** (atomic subtask): append строка в [`tasks/log/YYYY-MM.md`](tasks/log/2026-07.md) §Timeline + обновить §Последние события выше.  
Prose-архив: [`tasks/log/2026-07-legacy.md`](tasks/log/2026-07-legacy.md). **Не грузить** log на IMPLEMENT/TASK/QA.
