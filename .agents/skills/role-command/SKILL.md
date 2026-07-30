---
name: role-command
description: BACK IMPLEMENT, FRONT PLAN, INTEG GAP, IDEA PIPELINE — workflow router parity with Cursor/Claude Code. Загружать при любой role command.
---

# Role Command — Cursor / Claude Code parity

**Язык:** user-facing — **русский**. Subagent: «ответ и отчёт — на русском».

**FRONT:** тесты — **только parent**; spawn → HARD RULE из `front-tests-parent-only.mdc`.

**Claude Code:** делегирование `Agent` как обычно. Overlay: `explorer` · `verify` · `reviewer` + hooks + `.claude/instructions/spawn-hard.md`. Stop gate: `@verify` / `@reviewer` + QA Handoff.

Parse: `{PREFIX} {MODE}` or `{PREFIX} {MODE} FINISH`.

| Prefix | Role dir | Core | Isolation |
|--------|----------|------|-----------|
| BACK/FRONT/INTEG | `.cursor/rules/{back,front,integration}_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |

Multi-word: `ARCHIVE NOW`, `IDEA PIPELINE CONTINUE`, `INTEG GAP`, `INTEG GAP CLOSE`.

## Step 0 — graphify

`.cursor/rules/graphify.mdc` **до** Grep/Read codebase.

**Обязателен:** IMPLEMENT · TASK · BUGFIX · REFACTOR · QA; PM DISCOVER; TL SYNC DEV; brownfield VAN.  
**Пропуск:** greenfield VAN · PLAN · DECOMPOSE · CREATIVE · REFLECT · ARCHIVE · SECURITY · GAP (docs).

```bash
.venv/bin/graphify query|path|explain "…"
```

FINISH после code_changed: `.venv/bin/graphify update .`

## Step 0b — session / FINISH

`context-session-economy.mdc` §3; FINISH: `finish-block.mdc` → `finish-doc-router.mdc`.

**PLAN:** `SUSPENSION GUARD active — plan output unlimited` + token-economy §0.0.

## Step 1–3 — role chain

1. `{role_dir}mainrule.mdc` + `mainrule-core.mdc` (не корневой `mainrule-core` — его нет)
2. `{role_dir}workflow-{mode}.mdc` — MODE lowercase, **без** префикса роли. **ЗАПРЕЩЕНО:** `workflow-{role}-{mode}.mdc`
3. **Gates** из workflow → `{role_dir}isolation_rules/_lean/<mode>.mdc` (не `_lean/` без `isolation_rules/`)

## Step 4–6 — execute

- `memory-bank/` (lowercase); IMPLEMENT/TASK/QA: `load_now` only
- Skills: **только** из workflow (не сканировать каталог)
- §0.11 перед FINISH

## Acknowledgement

`OK {PREFIX} {MODE} — начинаю` (+ SUSPENSION GUARD для PLAN/brownfield VAN).

IMPLEMENT FINISH: `finish-block.mdc` — step + Handoff **до** decompose completed.

## IDEA PIPELINE

`workflow-idea-pipeline.mdc` → `memory-bank/idea/idea-<slug>.md`
