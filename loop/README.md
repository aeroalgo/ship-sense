# System loop — автоцикл (вне memory-bank)

Каталог **`loop/`** — автоматизация ролей. `memory-bank/` — артефакты; сюда loop **не** кладётся.

| | |
|--|--|
| **Гайд** | [`WORKFLOW.md`](WORKFLOW.md) |
| **Статус** | [`loop-state.yaml`](loop-state.yaml) |
| **Переходы** (next-mode owner) | [`transitions.yaml`](transitions.yaml) |
| **Session result** | `loop/runtime/{epic\|program}/result.yaml` |
| **State/trace** | `.claude/runtime/{epic\|program}/` |
| **FINISH агента** | `.cursor/rules/shared/finish-block.mdc` |
| **Runner** | `./loop/loop.sh` |
| **Diagnose** | `python3 .claude/hooks/loop_resolve.py doctor` · `halt-stats` |

```bash
./loop/loop.sh decompose-v1-p2-ship gpt
# INTEG: путь под integration/ → role=INTEG + program (GAP journey) сам
./loop/loop.sh decompose-portal gpt
./loop/loop.sh --id INTEG-… --gap … -m gpt   # явный override
python3 .claude/hooks/loop_resolve.py doctor
```

**DEPRECATED:** `./scripts/loop.sh` → redirect. Wrappers: `epic-loop.sh` / `program-loop.sh`.

Конфликт Handoff ↔ ledger → **loop-state.yaml**. Handoff ≠ event source. Next-mode не копировать в role workflow.
