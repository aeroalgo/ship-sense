# Role Command — Cursor parity chain

**Язык:** все user-facing сообщения — **русский** (@.claude/rules/language.md). Subagent/task prompts: добавь «ответ и отчёт пользователю — на русском».

**FRONT + любой frontend:** тесты (vitest/playwright/npm test/e2e) — **только parent**. Subagent spawn → в промпт вставить HARD RULE из `@.claude/rules/front-tests-parent-only.md` / `~/.claude/rules/02-front-tests-parent-only.md`.

**Claude Code:** делегирование через `Agent` как обычно. Overlay `.claude/agents/`: `explorer` · `verify` · `reviewer`.  
**Hooks spawn-gate:** `.claude/settings.json` + `.claude/hooks/*.py`. FINISH без `@verify` / QA без `@reviewer` / QA без Handoff — Stop hook блокирует.  
**Spawn HARD:** `.claude/instructions/spawn-hard.md` — для verify/reviewer packed секции + `ALLOW READ` ≤5 (иначе PreToolUse deny).

Parse: `{PREFIX} {MODE}` or `{PREFIX} {MODE} FINISH`.

| Prefix | Role dir | Core (полный путь) | Isolation |
|--------|----------|-------------------|-----------|
| BACK | `.cursor/rules/back_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |
| FRONT | `.cursor/rules/front_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |
| INTEG | `.cursor/rules/integration_developer/` | `{role_dir}mainrule-core.mdc` | `{role_dir}isolation_rules/_lean/<mode>.mdc` |

**Нет файла** `.cursor/rules/mainrule-core.mdc` — core только внутри `*_developer/`.

Multi-word: `ARCHIVE NOW`, `IDEA PIPELINE CONTINUE`, `INTEG GAP` (алиас `INTEGRATION GAP`), `INTEG GAP CLOSE` (алиас `INTEGRATION GAP CLOSE`).

## Step 0 — graphify (parity with Cursor `mainrule.mdc`)

Читай @.cursor/rules/graphify.mdc и ориентируйся по графу **до** Grep/Read по codebase.

**Обязателен** для: `IMPLEMENT` · `TASK` · `BUGFIX` · `REFACTOR` · `QA`; также `PM DISCOVER`, `TL SYNC DEV`; **brownfield** `BACK/FRONT/INTEG VAN`.

**Пропуск:** greenfield `VAN` · `PLAN` · `DECOMPOSE` · `CREATIVE` · `REFLECT` · `ARCHIVE NOW` · `SECURITY` · `GAP` (если только docs). CONTENT/MARKETING/SEO — пропускают.

**CLI (не в PATH):** всегда из **корня репо** (cwd = root; Shell `working_directory` = root). Канон только `<repo>/graphify-out/` — HARD RULE в @.cursor/rules/graphify.mdc.

```bash
.venv/bin/graphify query "<question>"
.venv/bin/graphify path "<A>" "<B>"
.venv/bin/graphify explain "<concept>"
```

Fallback на Read/Grep — только после ориентации по графу, или если root `graphify-out/graph.json` нет / stale. Не пропускай graphify «потому что файлы уже известны». В промпт каждого code-exploration subagent: «сначала `.venv/bin/graphify query|path|explain` из корня репо, затем Read/Grep; не создавать nested graphify-out».

**После правок кода (FINISH):** из корня репо `.venv/bin/graphify update .` — см. @.cursor/rules/shared/finish-block.mdc.

## Step 0b — session

1. @.cursor/rules/shared/context-session-economy.mdc §3
2. FINISH / `* FINISH`: @.cursor/rules/shared/finish-block.mdc → @.cursor/rules/shared/finish-doc-router.mdc (+ graphify update если code changed). IMPLEMENT: step-файл + Handoff **до** decompose/`load_now` (не дублировать чеклист здесь)
3. Tool unclear → recommend: **Cursor** + fast-editing (default) | **Claude Code** + premium-coding (E2E / multi-file / **any PLAN**)

### Если MODE = PLAN (BACK/FRONT/INTEG/PM)

**Сразу после acknowledgement** выведи в чат:

`SUSPENSION GUARD active — plan output unlimited`

- Читай `token-economy-core.mdc` §0.0 + §0.0.1 до записи артефакта
- Lean load ≠ lean write: **не** сжимай `plan-*.md` / `gap-*.md` под telegraph / 200 lines / chat brief
- PLAN → recommend premium model; after PLAN → new chat for IMPLEMENT

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
| SECURITY | `{role_dir}workflow-security.mdc` |
| GAP CLOSE | `{role_dir}workflow-gap-close.mdc` |

**ЗАПРЕЩЕНО угадывать:**
- `workflow-{role}-{mode}.mdc`
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

**Не** читай весь `isolation_rules_load.md` (каталог-справочник).  
Если Gates в workflow **нет** (BACK SECURITY) — lean не открывать.

Level — из decompose step / plan / task shard.  
**Скиллы не грузить из isolation** — только из workflow (Step 5).

## Step 4 — memory-bank

Каталог **строго** `memory-bank/` (lowercase).  
**ЗАПРЕЩЕНО:** `Memory-bank/`, `MEMORY-BANK/`.

Default (IMPLEMENT/TASK/QA): `memory-bank/activeContext.md` → `load_now` only. ONE task shard. ONE plan/domain shard if AC needs. См. Context-session-economy §3–4.

**PLAN override:** inventory по `workflow-*-plan.mdc` (для INTEG PLAN — все portal-relevant implement + routes). Не режь объём чтения «ради economy», если workflow требует полный registry.

## Step 5 — skills (lazy)

ONLY skills listed in the workflow file for current subtask. Do NOT scan skills catalog.

## Step 6 — execute

Follow workflow. BACK/FRONT QA → lean load §7 context-session-economy. Integration grep §0.11 token-economy before FINISH. Code modes: graphify Step 0 уже выполнен; FINISH → из корня репо `.venv/bin/graphify update .` если code changed.

## IDEA PIPELINE

@.cursor/rules/shared/workflow-idea-pipeline.mdc. Artifact: `memory-bank/idea/idea-<slug>.md`.

## Acknowledgement

`OK {PREFIX} {MODE} — начинаю`

Если MODE=PLAN: сразу вторая строка `SUSPENSION GUARD active — plan output unlimited`, затем читай `.claude/rules/plan-artifact.md`.

Если MODE=VAN и brownfield (есть код/compose): сразу `SUSPENSION GUARD active — architecture map output unlimited`, затем `.cursor/rules/shared/workflow-van-brownfield.mdc` + `.claude/rules/plan-artifact.md` (architecture paths).

Перед FINISH на PLAN: shell `wc -l` на plan-файл; TOC-only / слишком короткий → FAIL, дописать.  
Перед FINISH на brownfield VAN: architecture shards не stub-only; mermaid minimum (services + data-flow + erd|n/a).  
Перед FINISH на IMPLEMENT: @.cursor/rules/shared/finish-block.mdc — step-файл exists + Handoff шага **до** `decompose`=`completed`.

Slash-команды: `.claude/commands/` (см. `.claude/README.md`). Для portal wire предпочтительно **`/integ-plan`**. Полная as-built карта — **`/integ-van`**.
