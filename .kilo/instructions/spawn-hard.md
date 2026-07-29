# HARD — Task spawn (Kilo, без Orchestrator)

Orchestrator mode **deprecated**. Делегирование делает primary (`code` / `luna` / `grok` / `glm`) через tool **`task`**.

## Когда ОБЯЗАТЕЛЬНО вызвать `task` (не делать самому)

| Ситуация | Agent |
|----------|--------|
| Поиск по репо / «где X» (через graphify) | `explore` или `explorer` |
| Изолированная правка / подзадача реализации | `worker` или `general` |
| Review / QA prep read-only | `reviewer` |

**FAIL:** широкий grep/glob/read parent’ом вместо `task`→`explore` с GRAPHIFY query.

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
| **FORBID** | role-command; workflow read; recall; grep/glob; чужой эпик |

**FAIL:** prompt «реализуй s01 по shard» без AC/файлов/команд → worker сам читает workflow (раздувание).  
**FAIL:** worker вызывает `skill role-command` или Read `.cursor/rules/**` — parent уже передал контекст.

## IMPLEMENT L1–L2: parent без explore (HARD)

Если decompose **shard** уже в контексте parent и содержит L1/L2 + явные file paths:

| Делай parent | Не делай |
|--------------|----------|
| Сам: TDD red → edit → green targeted pytest | `task`→`explore` «найти структуру Alembic/файлы» |
| Или **один** `task`→`worker` с AC+paths+VERIFY в prompt | explore → worker → reviewer на один s01 |
| Read: shard + `pyproject.toml` + файлы из shard | Read decompose index + все sNN + чужой эпик |

**Explore обязателен только** когда parent не знает file:line и shard не даёт paths.

## Как вызывать (узкий prompt)

1. Tool `task`, agent = `explore`|`explorer`|`worker`|`general`|`reviewer`
2. В **prompt обязательно** (см. таблицу выше):
   - **GRAPHIFY:** (explore/reviewer) готовая строка для `query` / `path` / `explain`
   - **ALLOW paths:** ≤5 **файлов** (worker: shard + код; не деревья)
   - **FORBID:** `role-command`; Read `.cursor/rules/**`; `.agents/skills/**` (кроме явно вложенного в prompt); grep/rg/glob; `kilo_local_recall`; `apps/**`; лишний `memory-bank/**`
   - HARD RULE front-tests + «отчёт на русском»
3. Модель ребёнка pinned (flash) — не наследуй parent
4. Дождись summary

**FAIL parent prompt:** ALLOW = целое дерево (`apps/…/`, `tests/`) → ребёнок читает десятки файлов. Давай конкретные файлы.

Пример prompt:

```
Цель: найти цикл импорта BaseSourceConnector.
GRAPHIFY: query "BaseSourceConnector circular import config validator mqtt connector"
ALLOW: apps/edge/collector/src/collector/config/validator.py, apps/edge/collector/src/collector/domain/interfaces.py, apps/edge/collector/src/collector/plugins/mqtt/connector.py
FORBID: grep/rg/glob; kilo_local_recall; apps/**; frontend/; memory-bank/.
Budget: ≤3 graphify, ≤12 read. 1 файл=1 read. Не recall прошлых sessions.
Отчёт: file:line + цикл. На русском. HARD RULE: no frontend tests.
```

Пример **worker** (parent уже прочитал workflow + shard):

```
Цель: BACK IMPLEMENT s01-db-extensions — Alembic baseline.
AC: revision 001_extensions_timescale; upgrade CREATE EXTENSION timescaledb + uuid-ossp, schema shipsense; downgrade DROP SCHEMA shipsense CASCADE; include_schemas=True.
CREATE/EDIT: alembic.ini, migrations/env.py, migrations/versions/001_extensions_timescale.py
ALLOW READ: memory-bank/back/plan/decompose-v1-p1-storage/s01-db-extensions.md, pyproject.toml (+ файлы выше если уже есть)
VERIFY (сообщи parent, не полный suite): .venv/bin/alembic history
FORBID: role-command; Read .cursor/rules/**; Read .agents/skills/**; grep/glob; kilo_local_recall; memory-bank/** кроме shard; apps/**.
Budget: ≤15 read, ≤2 на файл. На русском. HARD RULE: no frontend tests.
```

## Budget (дети обязаны соблюдать)

| Agent | max steps | search | max read | re-read |
|-------|-----------|--------|----------|---------|
| explore / explorer | 18 | **только graphify** (≤3); grep/glob/**kilo_local_recall** deny | 12 | запрещён |
| worker / general | 22 | graphify если нужна ориентация; иначе Read ALLOW | 15 | ≤2 на файл |
| reviewer | 18 | graphify optional; иначе Read/diff ALLOW | 10 | запрещён; финал только текст |

Glob от корня / `rg` по всему репо / `kilo_local_recall` (дамп старых сессий) — **запрещены**.

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
- **BACK IMPLEMENT L1–L2** с shard + paths + pyproject в prompt → explore / reviewer «на всякий» (достаточно parent или один worker)
- Subagent вызывает **`skill role-command`**

## Resume при ошибке summary

`Tool call not allowed while generating summary: read`
→ `task` + `task_id=<child>` + «только финальный текстовый отчёт, без tools».
