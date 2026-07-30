# Epic loop — fresh session per Handoff

Автоцикл по `decompose-*/index.md`: после каждого FINISH/Handoff **процесс Claude завершается**, loop поднимает **новую** сессию (чистый контекст).

**По умолчанию — headless auto-chain** (`claude -p`, стрим в терминал + лог). `--interactive` = полный UI (после FINISH нужен `/exit` вручную).

## Зачем

Один чат = один atomic шаг (IMPLEMENT / CREATIVE / QA / BUGFIX). Эпик = очередь из Handoff `Следующий:` + `load_now`.

## Запуск

```bash
cd /path/to/ship-sense
./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e provider/your-model-id
./scripts/epic-loop.sh --interactive decompose-… provider/your-model-id
```

Или slash `/epic-run <decompose>` (arm) → в терминале `./scripts/epic-loop.sh [--model …]`.

## Env

| Var | Default | Meaning |
|-----|---------|---------|
| `EPIC_LOOP` | set by script | Stop-gate требует FINISH только в loop |
| `CLAUDE_BIN` | auto-detect | путь к `claude` |
| `EPIC_PERMISSION_MODE` | `dontAsk` | Bash/pytest/graphify/docker в scope проекта — через allowlist в `settings.local.json` (`Bash(*)`, `Edit(**)`). Перезапуск loop после правки permissions |
| `EPIC_CLAUDE_ARGS` | empty | доп. флаги после CLI-опций |
| `model` in state | from 2nd arg / `-m` | точное имя `claude --model` на весь эпик |
| `EPIC_ROLE` | `BACK` | fallback для `--role` |
| `EPIC_MAX` | `40` | fallback для `--max` |
| `EPIC_USE_INITIAL_MSG` | off | SessionStart `initialUserMessage` (loop и так передаёт `-p`) |

## State

`.claude/runtime/epic/state.json` (gitignore) + `next-prompt.txt`.

## Halt условия

- Handoff / context: `grill-me`, `needs_human`
- QA `blocked` и next не BUGFIX/QA
- fingerprint Handoff+load_now не изменился после сессии
- Stop×3 без FINISH / без Handoff
- mode вне `allowed_modes` (default: IMPLEMENT, CREATIVE, QA, BUGFIX)
- `max_iterations`

## Hooks

| Event | Role |
|-------|------|
| SessionStart | reminder EPIC MODE |
| Stop (`stop-gate.py`) | spawn gates + epic FINISH/Handoff gate |
| resolve/after | CLI для loop |

## Не делать

- Не крутить следующий sNN в той же сессии (Ralph-in-session) — съест контекст
- Не `--continue` / `-c` в loop
- Не spawn epic из subagent
