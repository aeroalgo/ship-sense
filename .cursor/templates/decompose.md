# DECOMPOSE — <plan_id> (legacy redirect)

**Устарело:** монолитный формат. Используй папку decompose + шаблоны:

| Артефакт | Шаблон |
|----------|--------|
| `decompose-<plan_id>/index.md` | [.cursor/templates/decompose/index.md](decompose/index.md) |
| `decompose-<plan_id>/sNN-<slug>.md` | [.cursor/templates/decompose/step.md](decompose/step.md) |

**Workflow:** `.cursor/rules/back_developer/workflow-decompose.mdc` · `.cursor/rules/front_developer/workflow-decompose.mdc`

**План:** [plan-<id>.md](../back/plan/plan-<id>.md) (или `../front/plan/plan-<id>.md`)
**Дата:** YYYY-MM-DD
**Режим:** BACK/FRONT DECOMPOSE
**Уровень:** L2 | L3 | L4

## Handoff

- **Next:** BACK/FRONT IMPLEMENT — первый `pending` шаг (s01)
- **load_now:** `back|front/plan/decompose-<plan_id>/s01-<slug>.md`
