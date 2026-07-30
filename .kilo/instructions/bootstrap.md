# Kilo bootstrap (slim — Cursor / Claude Code vibe)

Не дублируй `CLAUDE.md` в каждый ход. Канон workflow — файлы ниже + role-command.

| Тема | Куда |
|------|------|
| Role commands | `.claude/skills/role-command/SKILL.md` → `.cursor/rules/` |
| Kilo HARD (skills / FINISH / paths / spawn) | `.kilo/instructions/workflow-gate.md` |
| Subagent spawn | `.kilo/instructions/spawn-hard.md` |
| Session load | `memory-bank/activeContext.md` → только `load_now` |
| Язык | ответы пользователю — **русский**; в конце — модель |

**Session start once** (role command): role-command → core → workflow → gates → `activeContext` → ONE step → **creative reject check** → skills (full Read, no limit≈200) → work.  
**FINISH / «продолжай»:** §FINISH lean в `workflow-gate.md` — без перезапуска цепочки.  
**HARD:** `needs_creative` open → REJECT IMPLEMENT (не код). §0.5 «200 lines» = WRITE docs only.
