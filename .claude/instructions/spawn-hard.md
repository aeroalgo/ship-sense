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
| Перед FINISH (`code_changed: yes`) | **`@verify` ОБЯЗАТЕЛЬНО** (packed); FAIL/DENY → fix → retry до PASS; после PASS — не повторять |
| BACK QA после suite | **`@reviewer` ОБЯЗАТЕЛЬНО** (packed); pytest — у parent |
| Любой режим | доп. Agent — свободно |

### Search gate (`explorer`) — HARD

**Триггер (любой):** import/ownership audit · «где X» · multi-file map · поиск по `apps/`/`tests/` · неизвестные paths за пределами явного file list шага.

**Порядок:**
1. Read shard / plan (docs) — у parent
2. **Один раз** `Agent`→`explorer` (packed: Цель · GRAPHIFY · ALLOW ≤10)
3. Дальше parent работает по отчёту explorer (+ Read только названных file:line)

**FORBIDDEN parent до/вместо explorer:** серия `rg` / `grep -R` / широкий listing по `apps/` · `tests/` · `frontend/` как замена discovery.

**Исключение (explorer не нужен):** шаг правит **только** файлы из явного file list shard’а, discovery не требуется (1–few known paths, без audit/search).

**Исключение `delta_paths_exist` (HARD skip):** в prompt есть `## explorer (HARD)` + `delta_paths_exist: yes` (все path из `delta` на диске) → **`@explorer` SKIP**. Parent: Read только dirty_files + paths из delta/as_built. **FORBIDDEN:** Agent explorer / широкий search «на всякий случай».

**Канон type:** project overlay `explorer` (не built-in `Explore`) — graphify first, затем Grep/Glob/`rg` fallback до ответа.

**FAIL:** FINISH без `verify` когда `code_changed: yes`.  
**FAIL:** `@verify` повторно после `VERDICT: PASS` (retry только при `FAIL` / spawn DENY).  
**FAIL:** BACK QA FINISH без `Agent`→`reviewer`.  
**FAIL:** code-режим сделал широкий codebase search без предшествующего `Agent`→`explorer` в сессии (кроме исключения выше).  
**FAIL:** `isolation=worktree` / `model=` на verify|reviewer|explorer — hooks снимают.  
**FAIL:** spawn verify/reviewer/explorer без packed секций / ALLOW = дерево / >10 файлов / globs `**` в ALLOW.

### Verify retry (HARD)

```
Write implement step on disk → finalize result.yaml → @verify
  ├─ PASS → FINISH / stop (не повторять @verify)
  ├─ FAIL → parent чинит blockers → снова @verify
  └─ spawn DENY (stub / incomplete prompt / step missing) → починить → снова @verify
```

**DENY ≠ второй subagent:** `agent-pretool` отклоняет spawn до запуска; в логе может быть два `Agent verify` подряд — первый DENY, второй retry с packed prompt. Один успешный spawn = один verify.

**Step template (verify §6):** все роли — `.cursor/templates/implement/epic-step.yaml` (`schema: epic-implement/v1`, `role`, `checkpoints`; INTEG + `grep_control` · `verification_results` · `gaps`).

**Pre-FINISH validate-step:** `python3 .claude/hooks/epic_resolve.py validate-step --path <implement shard>` — exit 0 до finalize/`@verify` (тот же gate, что loop `after`).

**FORBIDDEN:** finalize/`@verify` до существования `implement-*/sNN-*.yaml` или `implement-*/eNN-*.yaml`.  
**FORBIDDEN:** `artifact:` = `plan/decompose-*` (только implement step path).

Hooks: `stop-gate` блокирует FINISH при FAIL; `agent-pretool` DENY `@verify` только если уже PASS.

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
| **RESULT** | — | да (result.yaml cross-check) | — |
| **ALLOW READ** | ≤10 | ≤10 | ≤10 |
| **FORBID** | edit; role-command; plan | edit; role-command; plan | edit; pytest; role-command; plan |

**FAIL:** «проверь шаг» / QA review / search без секций.  
**FAIL:** `ALLOW READ` = дерево / glob `dir/**` (нужны конкретные пути файлов, ≤10).

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
Отчёт: file:line + кто импортирует. На русском. Без plan-файла / Plan Mode.
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
VERIFY:
- .venv/bin/pytest tests/storage/test_time_axis.py::test_compute_official_ts -q
RESULT:
- path: loop/runtime/epic/result.yaml
- expect: status=ok ↔ VERIFY green; FAIL verify ⇒ нельзя status=ok
- note: parent: Write implement step → finalize result ДО spawn (не pending/draft; artifact существует); verify только читает
ALLOW READ: apps/edge/storage/time_axis.py, tests/storage/test_time_axis.py, apps/edge/storage/events_repo.py, loop/runtime/epic/result.yaml, memory-bank/back/implement/implement-<plan>/sNN-<slug>.yaml
FORBID: edit/write; role-command; plan.
Отчёт: VERDICT PASS|FAIL. На русском.
```

INTEG `eNN`: step shape — `epic-step.yaml` (`role: integ`). ALLOW READ: `memory-bank/integration/implement/implement-<plan>/eNN-<slug>.yaml`.

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
ALLOW READ: apps/edge/storage/writer.py, tests/storage/test_storage_contracts.py, pyproject.toml, docker-compose.yml, memory-bank/back/qa/<epic>/qa-YYYYMMDD-<slug>.yaml
FORBID: edit/write; pytest; .cursor/rules/**; Plan Mode / plan-файлы.
Отчёт: VERDICT PASS|BLOCKED|FAIL. На русском.
```

**FAIL parent QA:** suite есть, FINISH без `@reviewer` или без `## Handoff BACK QA` в `activeContext`.

## Budget (custom overlay)

| Agent | maxTurns | notes |
|-------|----------|-------|
| explorer | 40 | ищет до ответа по Цели; Grep/Glob/`rg` OK после graphify |
| verify | 12 | ≤12 read · ≤10 ALLOW · re-read запрещён; VERDICT only |
| reviewer | 18 | ≤8 rg · ≤12 read · ≤10 ALLOW · re-read запрещён; финал только текст |

## Hooks

| Event | Эффект |
|-------|--------|
| PreToolUse Agent | HARD RULE на все Agent; strip worktree/model на overlay; deny неполного prompt на verify/reviewer/explorer |
| SubagentStop | verify/reviewer без `VERDICT:` → block |
| Stop | FINISH без verify / QA без reviewer / QA без Handoff → block |

State: `.claude/runtime/spawn-gate/<session>.json` (gitignore).
