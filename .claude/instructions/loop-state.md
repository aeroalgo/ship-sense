# Единый loop — pointer

**Гайд:** [`loop/WORKFLOW.md`](../../loop/WORKFLOW.md)  
**Runner:** `./loop/loop.sh`  
**Канон:** `loop/loop-state.yaml` · `loop/transitions.yaml`  
**Rule:** `.cursor/rules/shared/workflow-loop-state.mdc`  
**FINISH-чеклист:** `.cursor/rules/shared/finish-block.mdc`

## Owners

| Что | Где |
|-----|-----|
| next-mode | `transitions.yaml` + runner |
| курсор | `loop-state.yaml` (пишет runner) |
| исход сессии | `loop/runtime/…/result.yaml` (пишет агент) |
| FINISH steps | `finish-block.mdc` |
| session narrative | `activeContext.md` Handoff (не event source) |

**Runtime split:** `loop/runtime/` = result; `.claude/runtime/` = state/trace/logs.

## FINISH (сессия)

1. Write весь `activeContext` (load_now → 1× ## Handoff → ≤1× ## done)
2. Finalize `loop/runtime/epic|program/result.yaml`
3. Stop — runner `after` пишет ledger

**Не** патчить `loop-state.yaml` вручную. **Не** копировать next-mode цепочки в workflow.

Epic / program ops: `epic-loop.md` · `program-loop.md` (не политика переходов).
