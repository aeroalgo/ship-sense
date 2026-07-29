---
paths:
  - "**"
---

# Context economy — Claude Code (IMPLEMENT/TASK/BUGFIX)

Применяется при role commands BACK/FRONT/INTEG IMPLEMENT · TASK · BUGFIX.
**Не** применяется к PLAN / DECOMPOSE / gap-*.md (там §0.0 — без лимитов).

## TodoWrite (HARD)

- **Максимум 2** TodoWrite за IMPLEMENT: 1× старт (plan), 1× FINISH (done)
- **Запрещено:** обновлять TodoWrite после каждого Edit / на каждый шаг реализации
- Decompose shard = уже готовый план — дублировать в todo = раздувание

## Re-read (HARD)

- Файл, который ты только что Read или Edit — **уже в контексте**. Не перечитывай
- Re-read допустим **только** при: `offset` за пределами первого чтения; после внешней правки другим tool
- `tasks/log/*.md`: читай **1×** за сессию для append; не перечитывай чтобы «убедиться»
- `activeContext.md`: читай **1×** старт + 1× если сам только что переписал (diff нужен)
- **Запрещено:** Read после Edit «чтобы проверить что записалось» — Edit идемпотентен

## find / grep vs graphify

- Для **codebase** (`app/`, `api/`, `core/`, `jobs/`, `tests/`, `frontend/`) сначала используй `.venv/bin/graphify query "..."` из корня репо
- `find` / `grep -R` по **кодовой** части репо без попытки graphify — нежелательны; используй их только как fallback, если graphify не покрывает запрос или явно недоступен
- Для `memory-bank/`, `.cursor/`, `.claude/`, `.kilo/`, `tasks/log/` и прочих **неиндексируемых / docs-only** зон fallback-поиск через `rg`, `Glob`, `ReadFile` разрешён сразу
- Предпочтение fallback: `rg` / `Glob` / `ReadFile`; shell `find` и `grep -R` — только если tool-поиск не решает задачу

## Workflow load (Session once)

За одну role-сессию каждый файл — Read **≤1×**:
- `role-command/SKILL.md`, `mainrule*.mdc`, `workflow-*.mdc`, `_lean/*.mdc`
- каждый `SKILL.md` из A∪B
- `activeContext.md` (повтор — только если сам переписал)

**FAIL:** повторный Read workflow «для уверенности» / после каждого крупного шага.

## Agent spawn — IMPLEMENT L1–L2

Не spawn Agent если parent уже прочитал decompose **shard** и shard содержит:
- уровень L1 или L2
- явные file paths create/edit
- deps/pyproject известны

Parent сам: TDD red → Edit/Write → green `.venv/bin/pytest` **или** один Task/Agent с упакованным prompt (AC + paths + VERIFY). Explorer + worker + reviewer на один L1 s01 = FAIL.
