# Implement index (epic hub)
**Plan ID:** <plan_id>
**Дата:** YYYY-MM-DD
**Режим:** BACK IMPLEMENT | FRONT IMPLEMENT

**Plan:** [plan-<id>.md](../../plan/plan-<id>.md)
**Decompose:** [decompose-<plan_id>/index.md](../../plan/decompose-<plan_id>/index.md)

Каждый шаг = один заход IMPLEMENT. Имена файлов совпадают с decompose: `sNN-<slug>.md`.

> **INTEG GAP / inventory:** грузить **этот index** (+ парный слой) → ходить **только по ссылкам** таблицы. **ЗАПРЕЩЕНО** глобить весь `back/implement/` / `front/implement/`.
> **Policy:** статусы живут только в `implement/sNN-*.md` и `decompose/index.md`. Этот файл — навигационный hub, без status-колонки.

## Реестр шагов (decompose ↔ implement)

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** | [s01-<slug>.md](../../plan/decompose-<plan_id>/s01-<slug>.md) | [s01-<slug>.md](s01-<slug>.md) |

Навигация и Handoff — только `activeContext.md`. Статусы шагов — `decompose/index.md` + `implement/sNN`.
