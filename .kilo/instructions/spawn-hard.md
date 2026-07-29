# HARD — Task spawn (Kilo, без Orchestrator)

Orchestrator mode **deprecated**. Делегирование делает primary (`code` / `luna` / `grok` / `glm`) через tool **`task`**.

## Когда ОБЯЗАТЕЛЬНО вызвать `task` (не делать самому)

| Ситуация | Agent |
|----------|--------|
| Поиск по репо / «где X» (через graphify) | `explore` или `explorer` |
| Изолированная правка / подзадача реализации | `worker` или `general` |
| TDD / написать-править тесты (red first) | `test-writer` |
| Multi-file surgical refactor (preserve behavior) | `refactor` |
| Root-cause bugfix (reproduce → fix → prove) | `bugfix` |
| Pre-FINISH gate (AC + VERIFY, read-only) | `verify` |
| Review / QA prep read-only | `reviewer` |

**FAIL:** широкий grep/glob/read parent’ом вместо `task`→`explore` с GRAPHIFY query.  
**FAIL:** один `worker` на всё подряд, когда задача = тесты / refactor / bugfix / verify — бери узкий agent.

## Parent packs context (HARD)

**Workflow chain (`role-command`, `mainrule*`, `workflow-*`, gates, skills) — только у parent, 1× за сессию.**

Subagent **не** повторяет workflow. Parent после своего Read **вкладывает в task prompt** готовый контекст:

| Блок | Что parent кладёт в prompt (кратко, не «прочитай workflow») |
|------|-------------------------------------------------------------|
| **Цель** | 1–2 предложения |
| **AC** | bullets из decompose step (acceptance criteria) |
| **Файлы** | create/edit paths + ALLOW read list |
| **Команды** | `.venv/bin/pytest …`, `alembic …` — точные строки |
| **Constraints** | tdd yes/no, no comments, SQL shape, revision id |
| **GRAPHIFY** | только explore/reviewer при необходимости |
| **FORBID** | role-command; workflow; plan-*.md; recall; grep/glob; чужой эпик |

**FAIL:** prompt «реализуй s01 по shard» без AC/файлов/команд → worker сам читает workflow (раздувание).  
**FAIL:** worker вызывает `skill role-command` или Read `.cursor/rules/**` — parent уже передал контекст.  
**FAIL:** worker Read `plan-*.md` / decompose index / `activeContext` — AC должен быть в prompt.  
**FAIL:** parent Read `plan-*.md` целиком на IMPLEMENT — только §/offset из shard.

## IMPLEMENT L1–L2: parent без explore (HARD)

Если decompose **shard** уже в контексте parent и содержит L1/L2 + явные file paths:

| Делай parent | Не делай |
|--------------|----------|
| Сам: TDD red → edit → green targeted pytest | `task`→`explore` «найти структуру Alembic/файлы» |
| Или **один** `task`→`worker` с AC+paths+VERIFY в prompt | explore → worker → reviewer на один s01 |
| Read: shard + `pyproject.toml` + ≤3 кода из shard | Read `plan-*.md` целиком; все sNN; чужой эпик; re-read |

**Explore обязателен только** когда parent не знает file:line и shard не даёт paths.

**Предпочтение storage s08–s11:** parent сам (узкий service + TDD), без worker.

## Как вызывать (узкий prompt)

1. Tool `task`, agent = `explore`|`explorer`|`worker`|`general`|`test-writer`|`refactor`|`bugfix`|`verify`|`reviewer`
2. В **prompt обязательно** (см. таблицу выше):
   - **GRAPHIFY:** (explore/reviewer) готовая строка для `query` / `path` / `explain`
   - **ALLOW paths:** ≤5 **файлов** (worker: код + tests; **не** plan; **не** деревья)
   - **FORBID:** `role-command`; Read `.cursor/rules/**`; `.agents/skills/**`; `plan-*.md`; `activeContext`; grep/rg/glob/`os.walk`; `kilo_local_recall`; лишний `memory-bank/**`
   - **Budget:** ≤8 read; 1 файл ≤1× (edit target ≤2×)
   - HARD RULE front-tests + «отчёт на русском»
3. Модель ребёнка pinned (flash) — не наследуй parent
4. Дождись summary

**FAIL parent prompt:** ALLOW = целое дерево (`apps/…/`, `tests/`) → ребёнок читает десятки файлов. Давай конкретные файлы.  
**FAIL parent prompt:** «прочитай shard / plan и сделай» — AC должен быть уже в тексте prompt.

Пример prompt:

```
Цель: найти цикл импорта BaseSourceConnector.
GRAPHIFY: query "BaseSourceConnector circular import config validator mqtt connector"
ALLOW: apps/edge/collector/src/collector/config/validator.py, apps/edge/collector/src/collector/domain/interfaces.py, apps/edge/collector/src/collector/plugins/mqtt/connector.py
FORBID: grep/rg/glob; kilo_local_recall; apps/**; frontend/; memory-bank/; plan-*.md.
Budget: ≤3 graphify, ≤8 read. 1 файл=1 read. Не recall прошлых sessions.
Отчёт: file:line + цикл. На русском. HARD RULE: no frontend tests.
```

Пример **worker** (parent уже прочитал workflow + shard; AC вставлен текстом):

```
Цель: TimeAxisService s08 — compute_official_ts + clock_shift detect/record.
AC:
- compute: prefer source if quality good and |skew|<max_skew_sec; bad year → edge + time_bad
- detect: backward_jump_sec=60, forward_jump_sec=300
- record: event clock_shift + clock_shift_log via EventsRepo
CREATE/EDIT: apps/edge/storage/time_axis.py, tests/storage/test_time_axis.py
ALLOW READ: apps/edge/storage/events_repo.py, apps/edge/storage/schemas.py
VERIFY: .venv/bin/pytest tests/storage/test_time_axis.py -q
FORBID: role-command; .cursor/**; .agents/**; plan-*.md; activeContext; decompose index; memory-bank/**; grep/glob/os.walk; re-read.
Budget: ≤8 read, ≤5 files, 1 файл ≤1× (edit ≤2×). На русском. HARD RULE: no frontend tests.
```

Пример **test-writer**:

```
Цель: red tests для TimeAxisService.compute_official_ts.
AC:
- prefer source when quality good and |skew|<max_skew_sec
- bad year → edge + time_bad
CREATE/EDIT: tests/storage/test_time_axis.py
ALLOW READ: apps/edge/storage/time_axis.py, apps/edge/storage/schemas.py
VERIFY: .venv/bin/pytest tests/storage/test_time_axis.py -q
FORBID: role-command; plan; activeContext; grep/glob; frontend suite.
Budget: ≤8 read, ≤5 files. Red first. На русском.
```

Пример **bugfix**:

```
Цель: починить failing test_clock_shift_backward.
AC: root cause + minimal fix; test green ≥1×
REPRO/VERIFY: .venv/bin/pytest tests/storage/test_time_axis.py::test_clock_shift_backward -q
CREATE/EDIT: apps/edge/storage/time_axis.py
ALLOW READ: tests/storage/test_time_axis.py, apps/edge/storage/events_repo.py
FORBID: symptom patches; skip/xfail; role-command; plan; grep/glob.
Budget: ≤10 read, ≤5 files. Reproduce first. На русском.
```

Пример **verify** (pre-FINISH):

```
Цель: pre-FINISH gate s08.
AC:
- compute_official_ts …
- detect/record clock_shift …
ALLOW READ: apps/edge/storage/time_axis.py, tests/storage/test_time_axis.py
VERIFY: .venv/bin/pytest tests/storage/test_time_axis.py -q
FORBID: edit/write; role-command; plan.
Отчёт: VERDICT PASS|FAIL + blockers. На русском.
```

## Budget (дети обязаны соблюдать)

| Agent | max steps | search | max read | unique files | re-read |
|-------|-----------|--------|----------|--------------|---------|
| explore / explorer | 18 | **только graphify** (≤3); grep/glob/**kilo_local_recall** deny | 8 | ≤5 | запрещён |
| worker / general | **12** | нет explore; только Read ALLOW | **8** | **≤5** | ≤1 (edit target ≤2) |
| test-writer | **14** | нет; только ALLOW; red→VERIFY | **8** | **≤5** | ≤1 (edit ≤2) |
| refactor | **14** | нет; surgical; preserve behavior | **8** | **≤5** | ≤1 (edit ≤2) |
| bugfix | **16** | нет; reproduce→fix→prove | **10** | **≤5** | ≤1 (edit ≤2) |
| verify | **12** | read-only; AC↔VERIFY; no edit | **8** | **≤5** | запрещён; VERDICT only |
| reviewer | 18 | graphify optional; иначе Read/diff ALLOW | 8 | ≤5 | запрещён; финал только текст |

Glob от корня / `rg` по всему репо / `os.walk` / `kilo_local_recall` — **запрещены**.

## Search policy (explore)

1. Primary **и единственный** поиск: `.venv/bin/graphify query|path|explain` из корня репо
2. Read только пути из ответа graphify ∩ ALLOW
3. Native tools `grep`/`glob` у explore — **deny** (нет fallback на rg)
4. Graphify fail → отчёт `graphify_fail` parent’у (parent: `graphify update .` или сам узкий read)
5. Parent в task prompt: **GRAPHIFY:** строка query, не «погрепай X»

## Запрещено

- Ждать Orchestrator mode
- Spawn вложенных субагентов
- Task без ALLOW paths (широкий «исследуй репо»)
- ALLOW = дерево каталога (`apps/edge/collector/`, `tests/`) вместо ≤5 файлов
- `kilo_local_recall` / чтение прошлых sessionID «для контекста»
- Цепочка explore→worker→reviewer→explore на тот же баг без новых фактов
- BACK/FRONT **QA** с ясного AC → spawn explore «найти scope» (parent сам: load_now + diff + `.venv/bin/pytest`)
- **BACK IMPLEMENT L1–L2** с shard + paths + pyproject в контексте → explore / worker «на всякий» без packed AC
- Subagent вызывает **`skill role-command`**
- Subagent / parent на IMPLEMENT: Read **`plan-*.md` целиком**
- Re-read одного файла >2× за сессию child

## Resume при ошибке summary

`Tool call not allowed while generating summary: read`
→ `task` + `task_id=<child>` + «только финальный текстовый отчёт, без tools».
