---
name: role-command
description: BACK IMPLEMENT, FRONT PLAN, INTEG GAP, IDEA PIPELINE — workflow router parity with Cursor/Claude Code. Загружать при любой role command.
---

# Role Command — Cursor / Claude Code parity

**Язык:** все user-facing сообщения — **русский**. Subagent prompts: «ответ и отчёт пользователю — на русском».

**FRONT + любой frontend:** тесты (vitest/playwright/npm test/e2e) — **только parent**. Subagent spawn → HARD RULE из `.cursor/rules/front-tests-parent-only.mdc`.

**Субагенты:** `.claude/agents/` (`reviewer` · `verify` · `explorer`) + built-in. **Обязательные gate’ы** (packed — `.claude/instructions/spawn-hard.md`): codebase search → `@explorer`; FINISH + `code_changed` → `@verify`; BACK QA → `@reviewer`. Прочие Agent — свободно.

Parse: `{PREFIX} {MODE}` or `{PREFIX} {MODE} FINISH`.

| Prefix | Role dir | Core (полный путь) | Isolation |
|--------|----------|-------------------|-----------|
| BACK | `.cursor/rules/back_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |
| FRONT | `.cursor/rules/front_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |
| INTEG | `.cursor/rules/integration_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |

**Нет файла** `.cursor/rules/mainrule-core.mdc` — core только внутри `*_developer/`.

Multi-word: `ARCHIVE NOW`, `IDEA PIPELINE CONTINUE`, `INTEG GAP`, `INTEG GAP CLOSE`.

## Step 0 — graphify

Читай `.cursor/rules/graphify.mdc` **до** Grep/Read по codebase.

**Обязателен** для: `IMPLEMENT` · `TASK` · `BUGFIX` · `REFACTOR` · `QA`; также `PM DISCOVER`, `TL SYNC DEV`; **brownfield** `BACK/FRONT/INTEG VAN`.

**Пропуск:** greenfield `VAN` · `PLAN` · `DECOMPOSE` · `CREATIVE` · `REFLECT` · `ARCHIVE NOW` · `SECURITY` · `GAP` (docs only).

```bash
.venv/bin/graphify query "<question>"
.venv/bin/graphify path "<A>" "<B>"
.venv/bin/graphify explain "<concept>"
```

После правок кода (FINISH): `.venv/bin/graphify update .` из корня репо.

## Step 0b — session

1. `.cursor/rules/shared/context-session-economy.mdc` §3
2. FINISH: `.cursor/rules/shared/finish-block.mdc` → `finish-doc-router.mdc` (+ graphify update если code changed). IMPLEMENT: step + Handoff **до** decompose/`load_now`

### Если MODE = PLAN

Сразу выведи: `SUSPENSION GUARD active — plan output unlimited`

- `.cursor/rules/token-economy-core.mdc` §0.0 + §0.0.1
- Не сжимай `plan-*.md` / `gap-*.md`
- PLAN → premium parent / сильная модель

## Step 1 — role index + core

Читай **полные пути** (не basename без папки роли):

- индекс роли: `{role_dir}mainrule.mdc`
- core роли: `{role_dir}mainrule-core.mdc`

Примеры:  
`.cursor/rules/back_developer/mainrule.mdc`  
`.cursor/rules/back_developer/mainrule-core.mdc`

Корневой `.cursor/rules/mainrule.mdc` — только router-таблица.  
**Запрещено** открывать `.cursor/rules/mainrule-core.mdc` (такого файла нет).

## Step 2 — workflow

Шаблон (MODE в **lowercase**, **без** префикса роли):

`{role_dir}workflow-{mode}.mdc`

| Команда | Файл (канон) |
|---------|----------------|
| BACK BUGFIX | `.cursor/rules/back_developer/workflow-bugfix.mdc` |
| BACK IMPLEMENT | `.cursor/rules/back_developer/workflow-implement.mdc` |
| BACK QA | `.cursor/rules/back_developer/workflow-qa.mdc` |
| FRONT BUGFIX | `.cursor/rules/front_developer/workflow-bugfix.mdc` |
| INTEG GAP | `.cursor/rules/integration_developer/workflow-gap.mdc` |
| ARCHIVE NOW | `{role_dir}workflow-archive.mdc` |
| GAP CLOSE | `{role_dir}workflow-gap-close.mdc` |

**ЗАПРЕЩЕНО угадывать:**
- `workflow-back-bugfix.mdc` / `workflow-front-*.mdc` / `workflow-integ-*.mdc`
- `workflow-BACK-bugfix.mdc`
- любой путь с удвоенным префиксом роли в имени файла

Нет файла → `Glob` `workflow-*.mdc` в `{role_dir}`, не изобретай имя. Execute steps in order.

## Step 3 — isolation (step 1a)

Читай **только** путь из строки **Gates** в `workflow-*.mdc` (копируй дословно).

Канон BACK QA:
`.cursor/rules/back_developer/isolation_rules/_lean/qa.mdc`

**ЗАПРЕЩЕНО угадывать:**
- `.cursor/rules/back_developer/_lean/qa.mdc` (пропущен `isolation_rules/`)
- любой `*_developer/_lean/...` без `isolation_rules/`

Если Gates в workflow **нет** (BACK SECURITY) — lean не открывать.  
Нет файла → не Read повторно с «похожим» путём; проверь `isolation_rules_load.md`.

## Step 4 — memory-bank

Каталог **строго** `memory-bank/` (lowercase).  
**ЗАПРЕЩЕНО:** `Memory-bank/`, `MEMORY-BANK/`.

IMPLEMENT/TASK/QA: `memory-bank/activeContext.md` → `load_now` only. ONE task shard. ONE plan shard if AC needs.

PLAN override: полный inventory по `workflow-*-plan.mdc`.

## Step 5 — skills (lazy)

ONLY skills из workflow file. Do NOT scan `.agents/skills/` catalog.

## Step 6 — execute

Integration grep §0.11 token-economy before FINISH.

## Acknowledgement

`OK {PREFIX} {MODE} — начинаю`

Если MODE=PLAN: вторая строка `SUSPENSION GUARD active — plan output unlimited`.

Если MODE=VAN и brownfield: `SUSPENSION GUARD active — architecture map output unlimited` + `.cursor/rules/shared/workflow-van-brownfield.mdc`.

Перед FINISH на PLAN: `wc -l` на plan-файл.  
Перед FINISH на brownfield VAN: architecture не stub-only; mermaid minimum.  
Перед FINISH на IMPLEMENT: `finish-block.mdc` — step-файл + Handoff **до** decompose completed.

## IDEA PIPELINE

`.cursor/rules/shared/workflow-idea-pipeline.mdc`. Artifact: `memory-bank/idea/idea-<slug>.md`.
