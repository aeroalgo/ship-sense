# Реестр шагов (Decompose index)
**Plan ID:** <plan_id>
**План:** [plan-<id>.md](../plan-<id>.md) (или `../back/plan/plan-<id>.md`)
**Implement index:** [implement-<plan_id>/index.md](../../implement/implement-<plan_id>/index.md)
**Дата:** YYYY-MM-DD
**Режим:** BACK DECOMPOSE | FRONT DECOMPOSE

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали шага — в `sNN-<slug>.md` (шаблон: [step.md](step.md)). Интерфейсы в шагах — **lean** (имена/поля/наследование), без готового кода.

> **INTEG GAP:** грузить **этот index** (и/или implement index) → ходить только по ссылкам колонок. Не глобить весь `*/implement/`.
> **Policy:** статусы живут только здесь и в `implement/sNN|eNN-*.md`. `implement/index` — navigation hub без status.

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | структура шагов, атомарность |
| … | … |

**Per-step канон (не дублировать полные пути здесь):**
- **BACK:** в каждом `sNN` — `code_surface` + блок **Impl skills** (карта: `back_developer/workflow-decompose.mdc`)
- **FRONT:** в каждом `sNN` — **Impl skills** + `visible_ui` + **Design skills** (карта: `front_developer/workflow-decompose.mdc`)

Index — только общие skills сессии DECOMPOSE.

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-<slug>.md](s01-<slug>.md)<br>• кратко: файлы/суть | [s01…](../../implement/implement-<plan_id>/s01-<slug>.md) | no | yes | BACK/FRONT IMPLEMENT | pending |

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

## Summary-чеклист

- [ ] s01 — <title>
- [ ] s02 — <title>

## Handoff

- **Next:** BACK/FRONT IMPLEMENT — первый шаг со статусом `pending` или `active`
- **load_now:** `back|front/plan/decompose-<plan_id>/s01-<slug>.md` (файл первого шага, не index)
- **INTEG GAP вход:** этот index + парный слой implement/decompose index
