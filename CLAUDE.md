# 

## PLAN ARTIFACT OVERRIDE (читать первым — важнее economy)

При `* PLAN` / записи `memory-bank/**/plan-*.md` / `gap-*.md` / brownfield VAN → `memory-bank/architecture/**`:

- **ЗАПРЕЩЕНО** жать вывод плана/карты: telegraph, «max 3 sentences», лимит ~200 строк, «кратко для контекста»
- **ОБЯЗАТЕЛЬНО:** plan/architecture file = maximally detailed; chat reply может быть коротким
- Lean **load** ≠ lean **write**
- Сразу после OK: `SUSPENSION GUARD active — plan output unlimited` (PLAN) или `SUSPENSION GUARD active — architecture map output unlimited` (brownfield VAN)
- Path-rule: `.claude/rules/plan-artifact.md` (автоматически на plan/gap/architecture)
- INTEG: Prefer slash **`/integ-plan`** (self-contained acceptance, `wc -l` ≥ 400 или FAIL)

@.claude/rules/plan-artifact.md

## Язык (обязательно)

@.claude/rules/language.md

**Cursor, Claude Code и Kilo — один workflow.** Канон: `.cursor/rules/` + `memory-bank/`.  
Claude Code: `.claude/agents/` + `.claude/instructions/spawn-hard.md` + `.claude/hooks/` + `.claude/settings.json`.  
Kilo: `kilo.jsonc` + `.kilo/agent/` + `.kilo/instructions/{bootstrap,workflow-gate,spawn-hard}.md` + OmniRoute в `~/.config/kilo/kilo.jsonc`.

Token economy: @.cursor/rules/token-economy-core.mdc — для PLAN / architecture смотри **только §0.0 + §0.0.1**; §§0.2/0.5 **не применять** к `plan-*.md` / `architecture/**`.

@.cursor/rules/mainrule.mdc

## Parity (обязательно)

Команды `BACK *`, `FRONT *`, `INTEG *`, `PM *`, `TL *`, `CONTENT *`, `MARKETING *`, `SEO *`, `IDEA PIPELINE *` работают **идентично Cursor**:

1. Прочитай skill `.claude/skills/role-command/SKILL.md` и выполни цепочку **до** основной работы
2. **Step 0 graphify** (code modes): `@.cursor/rules/graphify.mdc` + CLI **`.venv/bin/graphify`** из **корня репо** (`query` / `path` / `explain`; после правок — `update .`). Канон только `<repo>/graphify-out/`. Не в PATH — только через `.venv/bin/`
3. Не импровизируй альтернативный процесс — только файлы из `.cursor/rules/`
4. Skills из workflow — только пути из шага workflow (`.agents/skills/`, не весь каталог)

**Slash-команды:** `.claude/commands/` — см. `.claude/README.md`. PLAN → `/integ-plan` / `/back-plan` / `/front-plan`.

## Session start

Триггеры: `continue project ` · role commands · `PM INIT` (архив)

1. `memory-bank/activeContext.md` → **`load_now` only** — **кроме `* PLAN`**: для PLAN читай inventory из соответствующего `workflow-*-plan.mdc` (portal implement + routes)
2. Handoff: `memory-bank/back/implement/implement-*.md` или `back/task/task-*.md` → §Handoff
3. IMPLEMENT/TASK: ONE task shard + ONE plan shard. **PLAN:** полный inventory по workflow, не «один shard»
4. Не опирайся на transcript — файлы = source of truth

## FINISH

Канон: @.cursor/rules/shared/finish-block.mdc → @.cursor/rules/shared/finish-doc-router.mdc → шаблон `.cursor/templates/finish-doc-router.md`.

1. **IMPLEMENT:** step-файл `implement-*/sNN|eNN-*.md` + `## Handoff` в `activeContext.md` **до** decompose `completed` / next `load_now` (5 точек + FAIL в finish-block)
2. Рекомендуй `/clear` когда §2 context-session-economy требует new chat
3. **PLAN:** перед FINISH — `wc -l` plan-файла; если ниже acceptance из `/integ-plan` или `plan-artifact.md` → дописать, не закрывать
4. **code_changed:** из корня репо `.venv/bin/graphify update .`

## Context economy — IMPLEMENT/TASK/BUGFIX

@.claude/rules/context-economy-cc.md

**Коротко (HARD):**
- **TodoWrite ≤2** за сессию (старт + FINISH); не обновлять на каждый шаг
- **Re-read запрещён** для файла, уже прочитанного / отредактированного в этой сессии
- Для codebase сначала **`.venv/bin/graphify query`**; для `memory-bank` / `.cursor` / `.claude` / `.kilo` разрешён fallback через `rg` / `Glob` / `ReadFile`
- Claude Code делегирует через `Agent` как обычно. Overlay: `@explorer` · `@verify` · `@reviewer`; перед FINISH при code_changed — **`@verify`**; BACK QA — **`@reviewer`** (`.claude/instructions/spawn-hard.md`)

## Stack (кратко)

| | |
|-|-|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic — `app/`, `api/`, `core/`, `jobs/` |
| Frontend | Next.js — `frontend/` |
| Tests | из корня репо: `.venv/bin/pytest` (не голый `pytest`; см. `pyproject.toml`) |
| DB/Redis | PostgreSQL 16, Redis 7 |

Детали: `memory-bank/techContext.md`

## User conventions (как Cursor user rules)

- Ответы на **русском**; в конце — модель ИИ
- Исправлять **причину** ошибок, не fallback и не скрытие
- Коммиты/PR — только по явному запросу
- Не править linter без запроса; не удалять неиспользуемые импорты
- SQL без переменных `@`
- Комментарии к коду — только по запросу
- `implement this` — gate для правок вне role command (см. token-economy §0.9)
- **FRONT TESTS = PARENT ONLY** (subagent **никогда** не запускает vitest/playwright/`npm test`/e2e) — `.claude/rules/front-tests-parent-only.md` / `.cursor/rules/front-tests-parent-only.mdc` (глобально: `~/.claude/rules/02-front-tests-parent-only.md`)

## Архив ролей

PM, TL, CONTENT, MARKETING, SEO → `_archive/cursor-rules/`. Команда `PM PLAN` → восстановить папку или читать workflow из архива.
