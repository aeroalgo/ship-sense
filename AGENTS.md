# ship-sense — agent workflow gate

Паритет **Cursor / Claude Code / Codex / Kilo**. Канон: `.cursor/rules/` + `memory-bank/`.

## Workflow router (обязательно)

При `BACK *`, `FRONT *`, `INTEG *`, `PM *`, `TL *`, `CONTENT *`, `MARKETING *`, `SEO *`, `IDEA PIPELINE *`:

1. Загрузи skill **`role-command`** (`.claude/skills/role-command/SKILL.md` или `.agents/skills/role-command/SKILL.md`)
2. Выполни цепочку skill **до** любой работы
3. Session start: `memory-bank/activeContext.md` → только `load_now`
4. Не импровизируй workflow — только файлы из `.cursor/rules/`

## Профили parent-сессии

| Режим | Codex | Kilo agent | Модель (OmniRoute) |
|-------|-------|------------|--------------------|
| PLAN / IMPLEMENT | `-p luna` | `luna` / `build` | `cx/gpt-5.6-luna` |
| PLAN / IMPLEMENT | `-p grok` | `grok` | `gc/grok-build` |
| PLAN / IMPLEMENT | `-p glm` | `glm` | `glm/glm-5.2` |
| лёгкий / cheap | `-p flash` | `flash` | `antigravity/gemini-3.5-flash-high` |

## Субагенты — только Gemini Flash (HARD)

| Agent | Модель | Назначение |
|-------|--------|------------|
| `explorer` | `antigravity/gemini-3.5-flash-low` | explore через **graphify** (не grep) |
| `worker` | `antigravity/gemini-3.5-flash-low` | implementation subtasks |
| `reviewer` | `antigravity/gemini-3.5-flash-high` | review, QA prep |

### Codex spawn

Spawn **только** через agent types из `.codex/agents/` / `~/.codex/agents/`:

1. `fork_turns = "none"` — **всегда**
2. `agent_type` = `explorer` | `worker` | `reviewer`
3. Явно `model` = flash-low или flash-high
4. `model_provider` = `omniroute`

**Запрещено:** spawn с `cx/*`, `gc/*`, `glm/*`, `kmc/*`, luna/sol/terra, `grok-build`; omit `fork_turns` / `fork_turns="all"`.

### Kilo spawn (Orchestrator deprecated)

Конфиг: `kilo.jsonc` + `.kilo/agent/*.md` + `.kilo/instructions/{bootstrap,workflow-gate,spawn-hard}.md`.  
`instructions[]` — slim (без AGENTS/CLAUDE каждый ход). FINISH lean / skills filter — в `workflow-gate.md`.  
Provider: **OmniRoute** (`~/.config/kilo/kilo.jsonc`).

Делегирует **primary** (`code`/`luna`/…) через tool `task` — отдельный Orchestrator не нужен.

1. Task → `explore`|`explorer` | `general`|`worker` | `reviewer`
2. Explore: **только graphify** (`.venv/bin/graphify`); grep/glob deny — см. `spawn-hard.md`
3. Sticky model на агенте (flash-low/high) — **не** наследуй parent
4. Built-in `explore`/`general` **включены** и переопределены на Flash (иначе Kilo не спавнит)
5. OmniRoute: `http://localhost:20128` + ключ `/home/aero/.codex/.omniroute_key`
6. Каталог моделей: `python3 .kilo/scripts/refresh-omniroute-models.py`
7. Ручной spawn: `@explore …` / `@worker …`

В промпт каждого subagent (Codex и Kilo) вставь HARD RULE из `.cursor/rules/front-tests-parent-only.mdc`.

## Gates

- `implement this` — обязателен для правок вне role command (`.cursor/rules/token-economy-core.mdc` §0.9)
- FRONT: subagent **никогда** не запускает vitest/playwright/npm test/e2e — только parent
- PLAN: `plan-*.md` / `gap-*.md` без лимита строк; `SUSPENSION GUARD active — plan output unlimited`
- FINISH: Handoff → `activeContext.md` → `.venv/bin/graphify update .` если code changed
- pytest: всегда из **корня репо** через `.venv/bin/pytest` (не голый `pytest` — в песочнице не работает)

## Stack

Python 3.12 FastAPI · SQLAlchemy 2 · Alembic · Next.js · `.venv/bin/pytest` · PostgreSQL 16 · Redis 7

## User conventions

- Ответы на русском; в конце — модель ИИ
- Исправлять причину ошибок, не fallback
- Коммиты/PR — только по явному запросу
- SQL без `@` переменных
- Комментарии к коду — только по запросу
