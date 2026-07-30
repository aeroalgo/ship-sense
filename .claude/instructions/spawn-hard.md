# HARD — Agent spawn (Claude Code): overlay gates

Claude Code **сам** делегирует через tool `Agent` как обычно (built-in `Explore` / `Plan` / `general-purpose` и любые другие типы, которые модель выберет).  
Мы **не** копируем kilo «parent сам / spawn запрещён» и **не** ломаем нативное делегирование.

Сверху навешаны только кастомные agents в `.claude/agents/`:

| `subagent_type` | Когда | Обязателен? |
|-----------------|-------|-------------|
| `explorer` | поиск «где X» (graphify → fallback Grep/Glob) | нет |
| `verify` | pre-FINISH при `code_changed: yes` | **да** |
| `reviewer` | BACK QA после suite | **да** |

## Политика

| Режим | Поведение |
|-------|-----------|
| IMPLEMENT / поиск / правки | Claude Code делегирует как обычно (`Agent` → built-in или `@explorer`) |
| Перед FINISH (`code_changed: yes`) | **`@verify` ОБЯЗАТЕЛЬНО** (packed prompt) |
| BACK QA после suite | **`@reviewer` ОБЯЗАТЕЛЬНО** (packed prompt) |
| «где X», экономия parent-модели | **`@explorer`** (опц.; haiku + graphify) |

**FAIL:** FINISH без `verify` когда `code_changed: yes`.  
**FAIL:** BACK QA FINISH без `Agent`→`reviewer`.  
**FAIL:** `isolation=worktree` / `model=` на verify|reviewer|explorer — hooks снимают.  
**FAIL:** spawn verify/reviewer без packed секций / ALLOW = дерево / >5 файлов.

Не запрещай built-in spawn. Не требуй «только parent сам».

## Parent packs context — только gate’ы (verify / reviewer)

Для `@verify` / `@reviewer` в `prompt` уже готовый контекст (workflow Read — у parent):

| Блок | verify | reviewer |
|------|--------|----------|
| **Цель** | да | да |
| **Suite results** | — | да |
| **AC+** | да | да |
| **AC−** | да (≥1) | да (≥1) |
| **§0.11** | да (≥1) | да (≥1) |
| **VERIFY** | да (имена pytest) | — |
| **ALLOW READ** | ≤5 файлов | ≤5 файлов |
| **FORBID** | edit; role-command; plan | edit; pytest; role-command; plan |

Для `@explorer` желательно: **Цель** · **GRAPHIFY:** · **ALLOW READ** (≤5). Без жёсткого PreToolUse deny — чтобы делегирование не стопорилось.

**FAIL:** «проверь шаг» / QA review без секций.  
**FAIL:** `ALLOW READ` = дерево.

## Как вызывать

1. Tool `Agent`, `subagent_type` = `explorer` | `verify` | `reviewer` (или built-in тип)
2. На custom overlay: не передавай `isolation` / `model` (pin в frontmatter)
3. Для verify/reviewer: секции с **новой строки** + HARD RULE front-tests + «отчёт на русском»
4. Дождись summary

### Пример explorer

```
Цель: где compute_official_ts и кто пишет clock_shift.
GRAPHIFY: query "compute_official_ts clock_shift TimeAxisService"
ALLOW READ: apps/edge/storage/time_axis.py, apps/edge/storage/events_repo.py
Отчёт: file:line. На русском.
```

### Пример verify (pre-FINISH)

```
Цель: pre-FINISH gate s08.
AC+:
- compute_official_ts prefer source when skew ok
AC−:
- не трогать quarantine / второй alembic head
§0.11:
- clock_shift event ↔ EventsRepo
ALLOW READ: apps/edge/storage/time_axis.py, tests/storage/test_time_axis.py, apps/edge/storage/events_repo.py
VERIFY:
- .venv/bin/pytest tests/storage/test_time_axis.py::test_compute_official_ts -q
FORBID: edit/write; role-command; plan.
Отчёт: VERDICT PASS|FAIL. На русском.
```

### Пример reviewer (BACK QA)

```
Цель: BACK QA review после suite (read-only).
Suite results:
- .venv/bin/pytest tests/storage/ -q → 65 passed
AC+:
- storage contracts + suite green
AC−:
- не объявлять full suite green если не завершён
§0.11:
- DATABASE_URL ↔ docker-compose.yml
ALLOW READ: apps/edge/storage/writer.py, tests/storage/test_storage_contracts.py, pyproject.toml, docker-compose.yml, memory-bank/back/qa/qa-YYYYMMDD-slug.md
FORBID: edit/write; pytest; .cursor/rules/**.
Отчёт: VERDICT PASS|BLOCKED|FAIL. На русском.
```

**FAIL parent QA:** suite есть, FINISH без `@reviewer` или без `## Handoff BACK QA` в `activeContext`.

## Budget (custom overlay)

| Agent | maxTurns | max read | unique files | re-read |
|-------|----------|----------|--------------|---------|
| explorer | 18 | 8 | ≤5 | запрещён |
| verify | 12 | 8 | ≤5 | запрещён; VERDICT only |
| reviewer | 18 | 8 | ≤5 | запрещён; финал только текст |

## Hooks

| Event | Эффект |
|-------|--------|
| PreToolUse Agent | HARD RULE на все Agent; strip worktree/model на overlay; deny неполного prompt **только** verify/reviewer |
| SubagentStop | verify/reviewer без `VERDICT:` → block |
| Stop | FINISH без verify / QA без reviewer / QA без Handoff → block |

State: `.claude/runtime/spawn-gate/<session>.json` (gitignore).

Built-in Agent calls hooks **не** переименовывают и **не** блокируют.
