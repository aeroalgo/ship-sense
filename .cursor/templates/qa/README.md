# Epic QA shard — `epic-qa/v1`

Канон: `epic-step.yaml` → `memory-bank/{back|front|integration}/qa/<epic>/qa-YYYYMMDD-<slug>.yaml`

- `verdict` — pass | fail | blocked (must match `result.yaml`)
- `scope[]`, `checks[]` — обязательны
- `fix_plan[]` — обязателен при fail/blocked (цепочка → BUGFIX)

Validate: `python3 .claude/hooks/epic_resolve.py validate-step --path <shard.yaml>`

Legacy `review.md` — human outline only; FINISH artifact = yaml.
