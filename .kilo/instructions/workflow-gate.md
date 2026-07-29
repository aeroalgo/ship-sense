# Kilo workflow gate (Cursor / Claude Code / Codex parity)

Ты работаешь в **Kilo Code** на репозитории ship-sense. Канон workflow тот же, что у Cursor и Claude Code.

## HARD — role commands

Если сообщение пользователя содержит (регистр не важен по смыслу, токены UPPERCASE):

`BACK` · `FRONT` · `INTEG` · `PM` · `TL` · `CONTENT` · `MARKETING` · `SEO` · `IDEA PIPELINE`

то **до любой работы** (один раз за сессию — см. §Session once):

1. Прочитай и выполни `.claude/skills/role-command/SKILL.md` (или `.agents/skills/role-command/SKILL.md`)
2. Не импровизируй процесс — только файлы из `.cursor/rules/` по цепочке skill
3. Session start: `memory-bank/activeContext.md` → только `load_now` (кроме `* PLAN` — inventory из workflow)

Core роли — **только** полный путь, например:
`.cursor/rules/back_developer/mainrule-core.mdc`  
**Нет** файла `.cursor/rules/mainrule-core.mdc` — не пытайся его открыть.

## HARD — Session once (anti re-read)

За **одну** role-сессию (до FINISH) каждый из этих файлов — **Read ≤1×**:

- `role-command/SKILL.md`
- `{role}/mainrule.mdc`, `{role}/mainrule-core.mdc`
- `workflow-{mode}.mdc`, isolation `_lean/{mode}.mdc`
- каждый `SKILL.md` из A∪B
- `memory-bank/activeContext.md` (повтор только если сам только что его переписал и нужен diff — иначе держи в контексте)

**FORBIDDEN:** `cat` / `python -c open()` / `head`/`tail`/`wc` / `find` вместо Read для уже известного пути; повторный Read «для уверенности»; искать `tasks.md` через find — канон `memory-bank/tasks.md`, log `memory-bank/tasks/log/`.

Tool result уже в контексте = источник истины. Re-read = FAIL vibe (раздувание).

### Re-read subagent (worker / reviewer) — HARD

- Файл уже Read в этой сессии → **не читай снова** (flash-low не держит контекст — это не оправдание)
- После Edit/Write файла → не перечитывай «убедиться» — операция идемпотентна
- `docker-compose.yml`, `README.md`, `alembic.ini` — 1× за сессию. При необходимости → offset
- Лимит на файл у subagent: `docker-compose` / крупный YAML / infra README — **≤2×** (до + после правки); иначе stop и текстовый отчёт parent'у

### TodoWrite (parent — IMPLEMENT/TASK/BUGFIX)

- **≤2** TodoWrite за сессию: 1× старт + 1× FINISH
- Запрещено обновлять чеклист на каждый шаг реализации — decompose shard = план
- Subagent: TodoWrite не вызывает (нет budget / права)

## HARD — skills (A∪B без раздувания)

Согласовано с Cursor / Claude Code: **слой B из decompose — канон, не вырезать**. Economy §3.7 режет **лишние** Read (re-read, false-предикаты A), не список в step.

1. **Слой B:** пути из `Impl skills` step — **Read каждый 1×** до кода (как Cursor/CC). Пустой B только если в step явно `—`.
2. **Слой A (workflow):** Read **только если предикат true** (не дублировать уже прочитанное из B):

| Skill | Читать когда (если ещё не в B / не Read) |
|-------|------------------------------------------|
| `tdd` · `python-testing-patterns` | в B **или** `tdd: yes` **или** правка `tests/` |
| `modern-python` | в B **или** Python-код в файлах шага |
| `fastapi-templates` | FastAPI / API routes в файлах шага |
| `supabase-postgres-best-practices` | SQL / Alembic / миграции |
| `python-anti-patterns` | в B **или** `code_surface`: service\|api |
| `requesting-code-review` · `verification-before-completion` | только Pre-FINISH; **skip** при docs-only / `code_changed: no` если AC уже сверен |

3. **Conflict:** «не пропускай A» = не пропускай **применимые** пункты A. Economy §3.7 > слепой Read всех `если` из A.  
4. Один `SKILL.md` — один Read. Не дублировать через tool `skill` + Read + bash.  
5. **FORBIDDEN:** удалять / обнулять `Impl skills` в decompose «ради economy» — ломает parity Cursor/CC.

## HARD — FINISH / «продолжай» (lean)

Триггеры: `FINISH` · `продолжай` · `continue` · handoff only · шаг уже done в этой сессии · пользователь просит только закрыть.

**FORBIDDEN:** заново role-command / mainrule / workflow-implement / isolation / полный A∪B; verify-cat после Edit; искать tasks через find/glob по репо.

**Бюджет ≤8 tool calls** (типично):

1. `activeContext.md` — 1× Read (если handoff ещё не в контексте)
2. implement/bugfix/qa shard + index — статусы (если ещё не done в контексте)
3. Edit/Write: Handoff в `activeContext` · append `memory-bank/tasks/log/` · `memory-bank/tasks.md` · status в decompose/implement index
4. `.venv/bin/graphify update .` — **только** если `code_changed: yes`

Канон шагов: `.cursor/rules/shared/finish-block.mdc` + `finish-doc-router.mdc` — Read **только если** ещё не читал в этой сессии; иначе действуй по уже известному чеклисту.

После правок — сразу краткий ответ на русском. Без повторного cat activeContext.

### IMPLEMENT status sync (HARD)

- Для BACK IMPLEMENT канон статуса = `memory-bank/back/plan/decompose-*/index.md`
- `implement/index.md` = **только навигация**, без `done` / `completed` / status suffix в строках
- Перед FINISH проверь 3 точки:
  1. текущий `sNN` в `decompose index` переведён в `completed`
  2. следующий шаг в `decompose index` остаётся `pending`
  3. `activeContext.md` переключён на следующий `sNN`
- Если обновлён implement step-файл, но не обновлён `decompose index` -> **FINISH запрещён**

## HARD — пути (Linux case-sensitive)

Канон **только** так:

| Канон | ЗАПРЕЩЕНО |
|-------|-----------|
| `memory-bank/...` | `Memory-bank/...`, `MEMORY-BANK/...` |
| `.cursor/rules/back_developer/isolation_rules/_lean/qa.mdc` | `.cursor/rules/back_developer/_lean/qa.mdc` (угадывание без `isolation_rules`) |
| `.cursor/rules/back_developer/workflow-bugfix.mdc` | `workflow-back-bugfix.mdc` (удвоенный префикс роли) |
| путь из строки **Gates** в `workflow-*.mdc` | склеивать `{role_dir}+_lean` самому |

Шаблон workflow: `workflow-{mode}.mdc` где mode = `bugfix`|`implement`|`qa`|… — **не** `workflow-back-{mode}`.

Перед Read: если сомневаешься — `Glob` / `ls`, не выдумывай регистр и сегменты пути.

Без цепочки role-command при **новом** role-сообщении — **FAIL**. При FINISH/продолжай — цепочку **не** перезапускать.

## HARD — субагенты (Orchestrator deprecated)

Делегирование: tool **`task`** у primary (`code`/`luna`/…). См. `.kilo/instructions/spawn-hard.md`.

**Parent packs context:** workflow/skills Read — **только parent**. В task prompt worker/reviewer — AC, paths, verify-команды из shard.

### FORBIDDEN subagent (любой child)

- **`skill role-command`** — цепочка role-command **только parent**, 1× за сессию
- Read `.cursor/rules/**`, `.agents/skills/**`, `role-command/SKILL.md`
- Повтор session start / graphify step 0 «для уверенности»
- Subagent **не** распознаёт `BACK IMPLEMENT` в user chat — только текст task prompt от parent

### IMPLEMENT L1–L2: без explore (parent)

**Не spawn explore**, если parent уже прочитал decompose **shard** и там есть:
- уровень L1 или L2 (или substep L2)
- явные пути create/edit в shard
- `pyproject.toml` / deps уже известны parent’у (или в shard)

**Parent сам:** red test → код → green targeted `.venv/bin/pytest` **или** один `task`→`worker` с **упакованным** prompt (AC + файлы + VERIFY).  
**Предпочтение** storage service-steps (s08–s11): parent сам, без worker.

**Explore только если:** «где в коде X» неизвестно · graphify нужен · shard без file paths · cross-package цикл импорта.

**FAIL parent:** explore + worker + reviewer на один L1/L2 s01 (Alembic baseline, один модуль, docs-only) — раздувание.  
**FAIL parent:** Read `plan-*.md` целиком на IMPLEMENT; re-read одного файла «для уверенности»; prompt worker «реализуй по shard» без AC в тексте.

| Agent | Модель | Назначение |
|-------|--------|------------|
| `explore` / `explorer` | flash-low | поиск через **graphify** (не grep) |
| `general` / `worker` | flash-low | implementation subtasks |
| `test-writer` | flash-low | TDD / тесты (red first) |
| `refactor` | flash-low | surgical multi-file refactor |
| `bugfix` | flash-high | root-cause: reproduce → fix → prove |
| `verify` | flash-high | pre-FINISH AC↔VERIFY (read-only) |
| `reviewer` | flash-high | review, QA prep |

`explore`/`general` — встроенные имена Kilo. `explorer`/`worker` — алиасы.
`test-writer` / `refactor` / `bugfix` / `verify` — task-specific system prompts.

В **task prompt** всегда: **GRAPHIFY query** + ALLOW **≤5 файлов** (не деревья) + budget ≤8 read.  
Explore = **только graphify**; `grep`/`glob`/`kilo_local_recall` deny. Детали: `.kilo/instructions/spawn-hard.md`.

**Запрещено:** наследовать Luna/Grok/GLM на children; ждать Orchestrator; ALLOW-дерево; `kilo_local_recall` чужих sessions; explore на BACK QA при ясном `load_now`; **explore на BACK IMPLEMENT L1–L2** когда shard + paths + pyproject уже у parent (см. §IMPLEMENT L1–L2 выше); worker без packed AC; Read `plan-*.md` целиком на IMPLEMENT.

В промпт **каждого** subagent вставь:

```
HARD RULE: ты subagent. НЕ запускай frontend-тесты (vitest/playwright/npm test/e2e).
Пиши/правь тестовые файлы если нужно. Запуск тестов — только у parent после твоего отчёта.
Ответ и отчёт parent — на русском.
```

## Parent профили (picker)

| Agent | Модель OmniRoute |
|-------|------------------|
| `luna` / `build` | `cx/gpt-5.6-luna` |
| `grok` | `gc/grok-build` |
| `glm` | `glm/glm-5.2` |
| `flash` | `antigravity/gemini-3.5-flash-high` |

Provider в picker: **OmniRoute** (`omniroute/...`). OmniRoute должен слушать `http://localhost:20128`.

## Gates

- `implement this` — для правок вне role command
- PLAN: `SUSPENSION GUARD active — plan output unlimited`; не жать `plan-*.md`
- FINISH: §FINISH lean выше; Handoff → `activeContext.md` → graphify update если code changed
- pytest: cwd = корень репо; всегда `.venv/bin/pytest …` — **FORBIDDEN** голый `pytest` (в песочнице не работает)
- Ответы пользователю — на русском; в конце — модель ИИ
