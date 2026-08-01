# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-api  
**План:** [plan-v1-p1-api.md](../plan-v1-p1-api.md)  
**Implement index:** [implement-v1-p1-api/index.md](../../implement/implement-v1-p1-api/index.md)  
**Дата:** 2026-07-30  
**Режим:** BACK DECOMPOSE  
**RF-01:** пути = `apps/api/app/...` (fastapi-templates); amend plan §13 выполнен в этом DECOMPOSE → r05 verify-only

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.yaml`. Интерфейсы — lean.

> **Policy:** статусы только здесь и в `implement/sNN-*.yaml`. `implement/index` — navigation hub без status.

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность sNN, file map, TDD cycle boundaries |

**Per-step канон:** skills gate — Core + situational из `.cursor/rules/back_developer/skills-gate-situational.mdc` (`workflow-decompose.mdc`).

## CREATIVE gates (closed) — CR-API-01..05 batch completed

Creative artifact: [creative-api-gates.md](../../creative/v1-p1-api/creative-api-gates.md) 

| ID | Блокирует | Артефакт (после CREATIVE) |
|----|-----------|---------------------------|
| CR-API-01 | s03 | [batch artifact](../../creative/v1-p1-api/creative-api-gates.md) ✅ |
| CR-API-02 | s06 | [batch artifact](../../creative/v1-p1-api/creative-api-gates.md) ✅ |
| CR-API-03 | s07 | [batch artifact](../../creative/v1-p1-api/creative-api-gates.md) ✅ |
| CR-API-04 | s04, s06 | [batch artifact](../../creative/v1-p1-api/creative-api-gates.md) ✅ |
| CR-API-05 | s08 | [batch artifact](../../creative/v1-p1-api/creative-api-gates.md) ✅ |

**Завершено:** `BACK CREATIVE` batch CR-API-01..05 → [creative-api-gates.md](../../creative/v1-p1-api/creative-api-gates.md)

**Следующая команда:** `BACK QA v1-p1-api`

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-scaffold.yaml](s01-scaffold.yaml)<br>• OpenAPI factory, envelope, DI, docker | [s01…](../../implement/implement-v1-p1-api/s01-scaffold.yaml) | no | yes | BACK IMPLEMENT | done |
| **s02** | [s02-assets-tree.yaml](s02-assets-tree.yaml)<br>• GET /api/assets/tree + aggregate status | [s02…](../../implement/implement-v1-p1-api/s02-assets-tree.yaml) | no | yes | BACK IMPLEMENT | done |
| **s03** | [s03-series-downsample.yaml](s03-series-downsample.yaml)<br>• GET /api/series + aggregate | [s03…](../../implement/implement-v1-p1-api/s03-series-downsample.yaml) | no — CR-API-01 closed | yes | BACK IMPLEMENT | done |Исправление статуса s03 после targeted green тестов|
| **s04** | [s04-events-rest.yaml](s04-events-rest.yaml)<br>• GET /api/events keyset | [s04…](../../implement/implement-v1-p1-api/s04-events-rest.yaml) | no — CR-API-04 closed | yes | BACK IMPLEMENT | done | Реализован GET /api/events, cursor, filters; targeted 7 passed |
| **s05** | [s05-setpoints.yaml](s05-setpoints.yaml)<br>• GET setpoints + history YAML | [s05…](../../implement/implement-v1-p1-api/s05-setpoints.yaml) | no | yes | BACK IMPLEMENT | done | Реализованы endpoints и YAML fixture; targeted 4 passed |
| **s06** | [s06-ws-fanout.yaml](s06-ws-fanout.yaml)<br>• WS /api/stream + FanoutBridge | [s06…](../../implement/implement-v1-p1-api/s06-ws-fanout.yaml) | no — CR-API-02/04 closed | yes | BACK IMPLEMENT | done | Реализованы WS protocol/ring/manager/bridge; targeted 3 passed |

| **s07** | [s07-session-b11.yaml](s07-session-b11.yaml)<br>• roster + POST/DELETE session → B6 | [s07…](../../implement/implement-v1-p1-api/s07-session-b11.yaml) | no — CR-API-03 closed | yes | BACK IMPLEMENT | done | Реализованы roster/session lifecycle, cookie и B6 audit events |

| **s08** | [s08-reports-watch.yaml](s08-reports-watch.yaml)<br>• reports list + watch stub | [s08…](../../implement/implement-v1-p1-api/s08-reports-watch.yaml) | no — CR-API-05 closed | yes | BACK IMPLEMENT | completed | Реализованы reports catalog/watch JSON+HTML, deterministic verdict и data-quality |
| **s09** | [s09-health-sources-rate.yaml](s09-health-sources-rate.yaml)<br>• health/sources + rate limit | [s09…](../../implement/implement-v1-p1-api/s09-health-sources-rate.yaml) | no | yes | BACK IMPLEMENT | done | Реализованы health/sources status и in-memory rate limit; targeted 4 passed |
| **s10** | [s10-tests-i1-openapi.yaml](s10-tests-i1-openapi.yaml)<br>• I1 audit + OpenAPI completeness | [s10…](../../implement/implement-v1-p1-api/s10-tests-i1-openapi.yaml) | no | yes | BACK IMPLEMENT | completed |I1 import audit и OpenAPI completeness suite green|

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

## Summary-чеклист

- [x] s01 — scaffold FastAPI OpenAPI / envelope / DI
- [x] s02 — assets tree + aggregate status
- [x] s03 — series + downsample (CR-API-01 closed)
- [x] s04 — events REST keyset (CR-API-04 closed)
- [x] s05 — setpoints read YAML
- [x] s06 — WS fanout (CR-API-02/04 closed)
- [x] s07 — session B11 (CR-API-03 closed)
- [x] s08 — reports watch stub (CR-API-05 closed)
- [x] s09 — health sources + rate limit
- [x] s10 — I1 audit + OpenAPI suite

## Порядок без CREATIVE

`s01` → `s02` → `s05` → (CREATIVE) → `s03`/`s04`/`s06`/`s07`/`s08` → `s09` → `s10`

## Handoff

- **Next:** `BACK QA v1-p1-api` (s01–s10 done)
- **load_now:** `memory-bank/back/implement/implement-v1-p1-api/index.md` + plan AC
- **Сделано:** s01–s10 completed; creative CR-API-01..05 closed.
- **Epic loop:** next = QA → BUGFIX↔QA → REFLECT; ARCHIVE NOW вручную.
- **INTEG GAP вход:** этот index + implement index после QA pass
