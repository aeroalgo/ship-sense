# Implement index (epic hub)
**Plan ID:** <plan_id>
**Дата:** YYYY-MM-DD
**Режим:** BACK IMPLEMENT | FRONT IMPLEMENT | INTEG IMPLEMENT

**Plan:** [plan-<id>.md](../../plan/plan-<id>.md)
**Decompose:** [decompose-<plan_id>/index.md](../../plan/decompose-<plan_id>/index.md)

Каждый шаг = один заход IMPLEMENT. Имена shard = decompose: `sNN-<slug>.yaml` (BACK/FRONT) или `eNN-<slug>.yaml` (INTEG).

> **GAP / inventory:** грузить **этот index** (+ парный decompose index) → ходить **только по ссылкам** таблицы.
> **Policy:** статусы — `decompose/index.md` + `implement/sNN|eNN-*.yaml`. Этот файл — navigation hub, без status.

## Реестр шагов (decompose ↔ implement)

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** / **e01** | [s01-<slug>.yaml](../../plan/decompose-<plan_id>/s01-<slug>.yaml) | [s01-<slug>.yaml](s01-<slug>.yaml) |

Шаблон shard: [.cursor/templates/implement/epic-step.yaml](../../../implement/epic-step.yaml)

Навигация и Handoff — `activeContext.md`. Статусы — `decompose/index.md` + yaml shard.
