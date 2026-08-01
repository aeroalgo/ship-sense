# Реестр шагов (REFACTOR Decompose)
**Epic ID:** rf-fastapi-template-ownership  
**Task ID:** RF-01  
**План:** [plan-rf-fastapi-template-ownership.md](../plan-rf-fastapi-template-ownership.md)  
**Analysis:** [analysis-rf-fastapi-template-ownership.md](../analysis-rf-fastapi-template-ownership.md)  
**Implement index:** [implement-rf-fastapi-template-ownership/index.md](../../implement/implement-rf-fastapi-template-ownership/index.md)  
**Дата:** 2026-07-30  
**Режим:** BACK REFACTOR DECOMPOSE  
**Scope:** M/L  
**Behavior freeze:** IPC wire · Quality/EventSeverity · DB ORM · connector semantics

Каждый шаг — один заход `BACK REFACTOR @rNN`. Детали — в `rNN-*.md`. Интерфейсы — **lean** (без тел/полного кода).

> **Трекер шагов:** только этот index (не дублировать status-чеклисты rNN в plan).  
> **Не** путать с feature `sNN` / `back/plan/decompose-*`.

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность rNN, files/AC/TDD boundaries |

**Per-step канон** (не дублировать пути здесь): каждый `rNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.  
**Execute (не DECOMPOSE):** skills из `workflow-refactor.mdc` + Impl skills шага.

| `code_surface` | Шаги |
|----------------|------|
| `api` | r01 (+ fastapi-templates + anti-patterns) |
| `service` | r02, r03 (+ anti-patterns) |
| `test` | r04 |
| `infra` | r05 (docs, tdd:no), r06 |

## CREATIVE blockers

Нет. Behavior freeze; смена поведения → STOP → IMPLEMENT/BUGFIX/CREATIVE.

## Зависимости codebase (verified 2026-07-30)

- `apps/api/` — **отсутствует** (создаётся r01)
- Канон: `collector.domain.models` — Quality, TelemetrySample, Event*, Raw*, health
- Storage/pipeline импортируют канон из collector path
- `apps/edge/semantic/` — ship-pack models/engine
- T-003 decompose описывает `apps/edge/api` — **устаревает** до r05

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **r01** | [r01-scaffold-apps-api.md](r01-scaffold-apps-api.md)<br>• `apps/api` skill tree, pythonpath, health stub | [r01…](../../implement/implement-rf-fastapi-template-ownership/r01-scaffold-apps-api.yaml) | no | yes | BACK REFACTOR | done |
| **r02** | [r02-move-canonical-models.md](r02-move-canonical-models.md)<br>• Quality/TelemetrySample/Event* → app.*; split Raw*/health; rewire | [r02…](../../implement/implement-rf-fastapi-template-ownership/r02-move-canonical-models.yaml) | no | yes | BACK REFACTOR | done |
| **r03** | [r03-move-semantic.md](r03-move-semantic.md)<br>• `apps.edge.semantic` → `app.semantic`; delete old pkg | [r03…](../../implement/implement-rf-fastapi-template-ownership/r03-move-semantic.yaml) | no | yes | BACK REFACTOR | done |
| **r04** | [r04-import-graph-audit.md](r04-import-graph-audit.md)<br>• audit tests + README domain ownership | [r04…](../../implement/implement-rf-fastapi-template-ownership/r04-import-graph-audit.yaml) | no | yes | BACK REFACTOR | done |
| **r05** | [r05-amend-t003-plan-paths.md](r05-amend-t003-plan-paths.md)<br>• plan-v1-p1-api + decompose s01–s10 → `apps/api` | [r05…](../../implement/implement-rf-fastapi-template-ownership/r05-amend-t003-plan-paths.yaml) | no | no | BACK REFACTOR | done |
| **r06** | [r06-migrations-stub-orm-policy.md](r06-migrations-stub-orm-policy.md)<br>• empty migrations stub; ORM остаётся storage | [r06…](../../implement/implement-rf-fastapi-template-ownership/r06-migrations-stub-orm-policy.yaml) | no | no | BACK REFACTOR | done |

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

## Порядок выполнения

```
r01 → r02 → r03 → r04 → r05 → r06
```

- r02 зависит от r01 (`app` package + pythonpath)
- r03 зависит от r01 (может идти после r02 или параллельно после r01 — **рекомендация: после r02**, меньше churn pythonpath/imports)
- r04 зависит от r02 + r03
- r05 зависит от r01 (пути существуют); **блокер T-003 IMPLEMENT:** r01+r02+r05
- r06 зависит от r01; Medium/optional относительно A–C

**Параллельность:** не параллелить r02/r03 в одном чате (широкий import rewrite).

## Summary-чеклист

- [x] r01 — Scaffold `apps/api` per fastapi-templates
- [x] r02 — Move canonical models + split collector domain
- [x] r03 — Move semantic → `app.semantic`
- [x] r04 — Import-graph audit tests + README
- [x] r05 — Amend T-003 plan/decompose paths
- [x] r06 — Migrations stub + ORM policy doc

## Handoff

- **Next:** `BACK QA rf-fastapi-template-ownership`
- **load_now:** `memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md` + epic plan AC
- **Epic loop:** `./scripts/epic-loop.sh memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership`
- **T-003:** IMPLEMENT s01 разблокирован по path после r01+r02+r05; r06 policy/stub завершён как optional шаг относительно A–C
- **Epic QA scope:** проверить r01–r06 behavior freeze, import ownership, storage ORM/Alembic ownership и backend suite
