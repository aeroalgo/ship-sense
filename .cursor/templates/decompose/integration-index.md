# Реестр шагов (INTEG DECOMPOSE — element-first)
**Plan ID:** <plan_id>
**План:** [plan-<id>.md](../plan-<id>.md)
**Implement index:** [implement-<plan_id>/index.md](../../implement/implement-<plan_id>/index.md)
**Дата:** YYYY-MM-DD
**Режим:** INTEG DECOMPOSE
**Scope:** portal | journey | section

Каждый шаг = **один UI-элемент или раздел страницы**. Контракт API — **lean** в `eNN-*.md` §Contract (keys/path/shape словами, без готового кода). Не читать `integration/gap/`, `integration/contracts/`.

**Трекер status eNN:** только `decompose/index.md` + `implement/eNN-*.md`. `implement-<plan_id>/index.md` — navigation hub без status. В `plan-INTEG-*.md` не дублировать чеклист статусов.

Шаблон шага: [integration-step.md](integration-step.md)  
Шаблон implement hub: [.cursor/templates/implement/integ-index.md](../implement/integ-index.md)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | структура шагов / атомарность |
| `query-builder` | list/filter endpoints в элементе |

## Очередь элементов

| step_id | title & element | implement | route | API | tdd | next_phase | status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **e01** | [e01-hero-search.md](e01-hero-search.md)<br>• `Hero` — поиск города | [e01…](../../implement/implement-<plan_id>/e01-hero-search.md) | `/` | none | no | INTEG IMPLEMENT | pending |
| **e04** | [e04-catalog-filter-bar.md](e04-catalog-filter-bar.md)<br>• `FilterBar` + список | — | `/catalog` | GET /activities | yes | INTEG IMPLEMENT | pending |

Статусы: `pending` | `active` | `done` | `blocked`

## Summary-чеклист

- [ ] e01 — Hero search redirect
- [ ] e04 — Catalog FilterBar live API

## Handoff

- **Next:** INTEG IMPLEMENT — первый `eNN` со статусом `pending` или `active`
- **load_now:** `integration/plan/decompose-<plan_id>/e01-<slug>.md` (файл первого элемента, не index)
- **Implement hub:** создаётся при первом `INTEG IMPLEMENT` эпика (или stub при DECOMPOSE)
