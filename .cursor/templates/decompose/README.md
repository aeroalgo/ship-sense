# Decompose templates

**Shard (BACK / FRONT / INTEG):** [epic-step.yaml](epic-step.yaml) — `schema: epic-decompose/v1`, `role: back|front|integ`

| Артефакт | Путь |
|----------|------|
| Hub | `decompose-<plan_id>/index.md` — [index.md](index.md) |
| Shard | `decompose-<plan_id>/sNN\|eNN-<slug>.yaml` |

**Validate:** `python3 .claude/hooks/epic_resolve.py validate-step --path <shard.yaml>`

**needs_creative (BACK/FRONT):** `no` | `yes (CR-…)` | `yes (CR-…) — **closed**` · index колонка `yes (CR-…) ✅` после close.
