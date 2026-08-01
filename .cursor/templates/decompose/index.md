# Реестр шагов (Decompose index)
**Plan ID:** <plan_id>
**План:** [plan-<id>.md](../plan-<id>.md)
**Implement index:** [implement-<plan_id>/index.md](../../implement/implement-<plan_id>/index.md)
**Дата:** YYYY-MM-DD
**Режим:** BACK DECOMPOSE | FRONT DECOMPOSE | INTEG DECOMPOSE

Каждый шаг — атомарная задача (BACK/FRONT: feature slice; INTEG: один UI-элемент). Shard: `sNN|eNN-<slug>.yaml` — [.cursor/templates/decompose/epic-step.yaml](epic-step.yaml).

> **Policy:** статусы только здесь + `implement/sNN|eNN-*.yaml`. `implement/index` — hub без status. Plan не дублирует чеклист шагов.

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | структура шагов, атомарность |
| `query-builder` | INTEG: list/filter endpoints |

**Per-step:** BACK/FRONT — skills gate в каждом `sNN` (`workflow-decompose.mdc`). INTEG — lean §Contract в `eNN`, без gap/contracts as input.

## Очередь шагов (BACK / FRONT)

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-<slug>.yaml](s01-<slug>.yaml) | [s01…](../../implement/implement-<plan_id>/s01-<slug>.yaml) | no | yes | BACK/FRONT IMPLEMENT | pending |

**needs_creative:** `no` | `yes (CR-…)` | `yes (CR-…) ✅` (= shard `yes (CR-…) — **closed**`)  
**FORBIDDEN:** `yes (done)` без CR-ID · `no (CR-… closed)`

## Очередь элементов (INTEG)

| step_id | title & element | implement | route | API | tdd | next_phase | status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **e01** | [e01-<slug>.yaml](e01-<slug>.yaml) | [e01…](../../implement/implement-<plan_id>/e01-<slug>.yaml) | `/` | none | no | INTEG IMPLEMENT | pending |

## Summary-чеклист

- [ ] s01 / e01 — <title>

## Handoff (snapshot)

- **Next:** `<ROLE> <MODE>` @target — tip / ledger
- **load_now:** tip shard `.yaml` (не index alone)
