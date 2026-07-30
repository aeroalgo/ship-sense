# HARD — Agent spawn (Claude Code): overlay gates

Parent **MAY** spawn любых Agent по нужде.  
**Обязательные** gate’ы: **explorer** (codebase search) · **verify** (pre-FINISH) · **reviewer** (BACK QA).

| `subagent_type` | Когда | Обязателен? |
|-----------------|-------|-------------|
| `explorer` | codebase search / discovery в code-режимах | **да** (см. ниже) |
| `verify` | pre-FINISH при `code_changed: yes` | **да** |
| `reviewer` | BACK QA после suite | **да** |
| built-in / др. | когда parent считает нужным | нет |

## Политика

| Режим | Поведение |
|-------|-----------|
| IMPLEMENT · REFACTOR · BUGFIX · TASK (code) | перед широким поиском по codebase → **`@explorer` ОБЯЗАТЕЛЬНО** (packed) |
| Перед FINISH (`code_changed: yes`) | **`@verify` ОБЯЗАТЕЛЬНО** (packed) |
| BACK QA после suite | **`@reviewer` ОБЯЗАТЕЛЬНО** (packed); pytest — у parent |
| Любой режим | доп. Agent — свободно |

### Search gate (`explorer`) — HARD

**Триггер (любой):** import/ownership audit · «где X» · multi-file map · поиск по `apps/`/`tests/` · неизвестные paths за пределами явного file list шага.

**Порядок:**
1. Read shard / plan (docs) — у parent
2. **Один раз** `Agent`→`explorer` (packed: Цель · GRAPHIFY · ALLOW ≤5)
3. Дальше parent работает по отчёту explorer (+ Read только названных file:line)

**FORBIDDEN parent до/вместо explorer:** серия `rg` / `grep -R` / широкий listing по `apps/` · `tests/` · `frontend/` как замена discovery.

**Исключение (explorer не нужен):** шаг правит **только** файлы из явного file list shard’а, discovery не требуется (1–few known paths, без audit/search).

**Канон type:** project overlay `explorer` (не built-in `Explore`) — graphify first, затем Grep/Glob/`rg` fallback до ответа.

**FAIL:** FINISH без `verify` когда `code_changed: yes`.  
**FAIL:** BACK QA FINISH без `Agent`→`reviewer`.  
**FAIL:** code-режим сделал широкий codebase search без предшествующего `Agent`→`explorer` в сессии (кроме исключения выше).  
**FAIL:** `isolation=worktree` / `model=` на verify|reviewer|explorer — hooks снимают.  
**FAIL:** spawn verify/reviewer/explorer без packed секций / ALLOW = дерево / >5 файлов.

Built-in Agent types hooks не блокируют и не переименовывают.

## Parent packs context — gate’ы

| Блок | explorer | verify | reviewer |
|------|----------|--------|----------|
| **Цель** | да | да | да |
| **GRAPHIFY** | да (query/path/explain) | — | — |
| **Suite results** | — | — | да |
| **AC+** | — | да | да |
| **AC−** | — | да (≥1) | да (≥1) |
| **§0.11** | — | да (≥1) | да (≥1) |
| **VERIFY** | — | да (имена pytest) | — |
| **ALLOW READ** | ≤5 | ≤5 | ≤5 |
| **FORBID** | edit; role-command; plan | edit; role-command; plan | edit; pytest; role-command; plan |

**FAIL:** «проверь шаг» / QA review / search без секций.  
**FAIL:** `ALLOW READ` = дерево.

## Как вызывать (gate)

1. Tool `Agent`, `subagent_type` = `explorer` | `verify` | `reviewer`
2. На custom overlay: не передавай `isolation` / `model` (pin в frontmatter)
3. Секции с **новой строки** + HARD RULE front-tests + «отчёт на русском»
4. Дождись summary

### Пример explorer (search gate)

```
Цель: import/ownership audit — где apps/api и collector тянут domain/FastAPI.
GRAPHIFY: query "apps/api app.telemetry collector.domain plugins FastAPI imports"
ALLOW READ: apps/api/app/main.py, apps/edge/collector/src/collector/domain/interfaces.py
Отчёт: file:line + кто импортирует. На русском.
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

| Agent | maxTurns | notes |
|-------|----------|-------|
| explorer | 40 | ищет до ответа по Цели; Grep/Glob/`rg` OK после graphify |
| verify | 12 | ≤8 read · ≤5 ALLOW · re-read запрещён; VERDICT only |
| reviewer | 18 | ≤8 rg · ≤10 read · ≤5 ALLOW · re-read запрещён; финал только текст |

## Hooks

| Event | Эффект |
|-------|--------|
| PreToolUse Agent | HARD RULE на все Agent; strip worktree/model на overlay; deny неполного prompt на verify/reviewer/explorer |
| SubagentStop | verify/reviewer без `VERDICT:` → block |
| Stop | FINISH без verify / QA без reviewer / QA без Handoff → block |

State: `.claude/runtime/spawn-gate/<session>.json` (gitignore).
