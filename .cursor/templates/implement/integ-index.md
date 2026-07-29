# Implement index (INTEG epic hub)
**Plan ID:** <plan_id>
**Дата:** YYYY-MM-DD
**Режим:** INTEG IMPLEMENT

**Plan:** [plan-<id>.md](../../plan/plan-<id>.md)
**Decompose:** [decompose-<plan_id>/index.md](../../plan/decompose-<plan_id>/index.md)

Каждый шаг = один заход `INTEG IMPLEMENT`. Имена файлов = decompose: `eNN-<slug>.md`.

> **Inventory / GAP CLOSE:** грузить **этот index** → ходить **только по ссылкам** таблицы. **ЗАПРЕЩЕНО** глобить весь flat `integration/implement/*`.
> **Policy:** статусы живут только в `implement/eNN-*.md` и `decompose/index.md`. Этот файл — navigation hub, без status-колонки.

## Реестр шагов (decompose ↔ implement)

| step | decompose | implement |
| :--- | :--- | :--- |
| **e01** | [e01-<slug>.md](../../plan/decompose-<plan_id>/e01-<slug>.md) | [e01-<slug>.md](e01-<slug>.md) |

## Handoff

- **Next:** `INTEG IMPLEMENT eNN` …
- **load_now:** конкретный `eNN-<slug>.md` (не этот index при wire)
- **Decompose tracker:** [decompose index](../../plan/decompose-<plan_id>/index.md)
