# Epic loop — fresh session per step

Автоцикл по `decompose-*/index.md` / journey: **единая точка** `./loop/loop.sh`  
(legacy: `epic-loop.sh` / `program-loop.sh` — обёртки).

После каждого FINISH процесс Claude завершается, loop поднимает **новую** сессию.

**По умолчанию — headless auto-chain** (`claude -p`). `--interactive` = полный UI (после FINISH нужен `/exit` вручную).

## Зачем

Один чат = один atomic шаг (IMPLEMENT / REFACTOR / SECURITY / CREATIVE / QA / BUGFIX / REFLECT).

**Канон курсора / next-mode:**
- ledger: `loop/loop-state.yaml`
- transitions: `loop/transitions.yaml` (+ runner `after`)
- session event: `loop/runtime/{epic|program}/result.yaml`
- FINISH-чеклист агента: `.cursor/rules/shared/finish-block.mdc` (**не** копировать mode contracts сюда)
- правило: `.cursor/rules/shared/workflow-loop-state.mdc`
- гайд: `loop/WORKFLOW.md`

`activeContext.md` / `decompose-*/index.md` = session/human view.  
Handoff «Следующий» = narrative; при конфликте → **loop-state**.

**Runtime split:** `loop/runtime/` = result; `.claude/runtime/` = state/trace/logs.

**after_session:** `advance_ledger_after_session` · `resolve` — ledger-first `next.command`.

**ARCHIVE NOW — вручную** после `complete` (loop не запускает archive).

**activeContext:** ровно **один** `## Handoff` + ≤ один `## done` (FINISH = **Write весь файл**). Shape FAIL → halt.

**Paths:** epic-scoped CREATIVE/QA/BUGFIX → `{mode}/<epic_id>/`; ARCHIVE → `memory-bank/archive/{role}/`. Канон: `.cursor/rules/shared/epic-scoped-paths.mdc`.

**Cross-role journey:** `.claude/instructions/program-loop.md` · `./loop/loop.sh --track program`.

## Запуск

```bash
cd /path/to/ship-sense
./loop/loop.sh decompose-v1-p1-pipeline-db-e2e provider/your-model-id
./loop/loop.sh --interactive decompose-… provider/your-model-id
# legacy:
./loop/epic-loop.sh decompose-… provider/your-model-id
```

Или slash `/epic-run <decompose>` (arm) → в терминале `./loop/epic-loop.sh [--model …]`.

**REFACTOR:** arm на `memory-bank/{back|front|integration}/refactor/plan/decompose-<id>/`; pending считает `rNN`. FINISH artifact = `refactor/implement/implement-<id>/rNN-*.md`. Канон: `.cursor/rules/shared/workflow-refactor-epic.mdc`.

**SECURITY:** arm на `memory-bank/{back|front|integration}/security/plan/decompose-<id>/`; pending считает `aNN`. FINISH artifact = `security/implement/implement-<id>/aNN-*.md`. Цепочка: `* SECURITY PLAN` → `* SECURITY DECOMPOSE` → `* SECURITY` @aNN. Канон: `.cursor/rules/shared/workflow-security-epic.mdc`.

## Env

| Var | Default | Meaning |
|-----|---------|---------|
| `EPIC_LOOP` | set by script | Stop-gate требует FINISH только в loop |
| `CLAUDE_BIN` | auto-detect | путь к `claude` |
| `EPIC_PERMISSION_MODE` | `dontAsk` | allowlist в `settings.local.json`. `result.yaml` = `loop/runtime/…` |
| `EPIC_CLAUDE_ARGS` | empty | доп. флаги |
| `model` in state | from 2nd arg / `-m` | `claude --model` на весь эпик |
| `EPIC_ROLE` | `BACK` | fallback для `--role` |
| `EPIC_MAX` | `40` | fallback для `--max` |
| `EPIC_USE_INITIAL_MSG` | off | SessionStart `initialUserMessage` |

## State

`.claude/runtime/epic/state.json` (gitignore) + `next-prompt.txt`.  
Machine next: `loop/loop-state.yaml` ← runner после `result.yaml`.

## Halt / complete

**Halt:** grill-me / needs_human · fingerprint без прогресса · Stop×3 без FINISH · implement step не по шаблону · mode вне allowed · max_iterations · result/crosscheck FAIL (см. `finish-block` / engine).

**Complete:** после REFLECT transitions → ARCHIVE; ARCHIVE вручную (`* ARCHIVE NOW`).

## Hooks

| Event | Role |
|-------|------|
| SessionStart | reminder EPIC MODE |
| Stop (`stop-gate.py`) | spawn gates + epic fingerprint gate |
| Pre/Post Agent | spawn-gate verify/reviewer/explorer |
| resolve/after | CLI для loop |

## Не делать

- Не крутить следующий sNN в той же сессии
- Не `--continue` / `-c` в loop
- Не spawn epic из subagent
- Не копировать таблицы next-mode / mode contracts сюда — `transitions.yaml` + `finish-block.mdc`
