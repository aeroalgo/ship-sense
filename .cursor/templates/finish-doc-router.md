# FINISH — doc-router update

**Task:** T-xxx  
**Command:** BACK IMPLEMENT | QA | REFLECT | ARCHIVE | PLAN | VAN | INTEG …

Канон заполнения `activeContext.md`: **Write весь файл целиком** на FINISH.  
Структура: `## load_now` → **ровно один** `## Handoff …` → **≤ один** `## done — do NOT load`.  
**FAIL:** ≥2 `## Handoff` · ≥2 `## done` · sandwich (старый Handoff/done в хвосте) · completed shard в `load_now`.  
История шагов → `tasks/log/` + implement/qa/bugfix shards, **не** копилка в activeContext.  
Rules (`finish-doc-router.mdc`) дают **когда** и **By command** / graphify / Forbidden — не дублировать здесь.

## done (один короткий блок)

- [ ] Убрать completed shard из `load_now` (не оставлять с пометкой «не загружать»).
- [ ] В `## done — do NOT load` — **≤5** свежих ссылок (последний шаг + связанные creative). Не дублировать заголовок `## done`. Не тащить весь backlog эпика.

## Новый load_now (max 3)

1. next work shard — **путь к файлу**, не index: `decompose-*/sNN|eNN-*.yaml` · `bugfix-*.md` · `qa-*.yaml` · `task-*.md` (**только pending/active**, не completed)
2. при epic → QA: `implement-<id>/index.md` (навигация) — **без** `plan-*.md`
3. опц. qa-артефакт при re-run / BUGFIX из Fix plan

**FORBIDDEN в `load_now`:** полный `plan-*.md` · «acceptance context = plan» · completed shards  
**AC:** в step / Handoff Epic QA / Fix plan. Jump `plan §N` только если Consumes требует и shard неполон.  
**Исключение:** режим PLAN или вход DECOMPOSE — plan как объект работы OK до FINISH DECOMPOSE (после — tip `s01|e01`).

## load_if_needed (trim)

- … — только shards, релевантные **следующему** шагу; creative — только open CR; `plan §N` — jump, не целиком

## activeContext §Сейчас / §Следующий шаг

1. … — канон «где стоим»; без `focus/`

## tasks.md Index

- [ ] обновить колонки **Step**, **Status** и **Progress** для T-xxx
- [ ] **обязательно:** append строка в `tasks/log/YYYY-MM.md` (§Delivery log)

## Delivery log (обязательно)

Файл: `memory-bank/tasks/log/YYYY-MM.md` — append **одна строка** в таблицу §Timeline:

```markdown
| YYYY-MM-DD | T-xxx | BACK IMPLEMENT sNN | [sNN-slug.yaml](back/implement/.../sNN-slug.yaml) |
```

Также обновить §Последние события в `tasks.md` (последние 5 строк, без деталей).

**Когда:** FINISH с завершённым atomic subtask (IMPLEMENT sNN, PLAN, DECOMPOSE, CREATIVE, QA, BUGFIX, TASK).  
**Пропуск:** checkbox внутри того же шага; typo-only правки.

## Shard checkbox / implement (ORDER — до decompose completed)

- [ ] **Файл существует:** `memory-bank/{back|front|integration}/implement/implement-<plan>/sNN|eNN-<slug>.yaml`
- [x] Канон: `.cursor/templates/implement/epic-step.yaml` (`schema: epic-implement/v1`, `role`, `checkpoints`, FINISH только при все cp `done`)
- [ ] **ЗАПРЕЩЕНО** legacy `.md` implement shards и Handoff внутри yaml step
- [ ] **## Handoff** этого `sNN|eNN` уже в `activeContext.md` (шаг ниже) — **до** галки decompose

## Decompose index (если шаг из `decompose-*/`) — только после step + Handoff

- [ ] `status: completed` / `done` в `decompose-*/index.md` (**после** step-файла + Handoff)
- [ ] `[x]` в Summary-чеклисте  
  (не через `tasks.md`)
- [ ] `implement/index.md` — ссылки only, **без** `done`/`completed`/status suffix

## Handoff (только `activeContext.md`)

**HARD — Write whole file:** на FINISH записать **весь** `activeContext.md` инструментом Write (не partial Edit хвоста).  
После FINISH: **единственный** `## Handoff …`, **≤ один** `## done`. Старые Handoff **удалить**, не оставлять под done.  
**FORBIDDEN:** prepend/append; sandwich «новый Handoff + старый Handoff/done»; стопка done; completed в `load_now`; Handoff внутри implement step.  
Порядок: `## load_now` → **один** `## Handoff …` → `## done — do NOT load` (опционально, один).  
Писать **после** `@verify` PASS и **до** sync decompose как часть того же FINISH.

**result.yaml (обязательно в том же FINISH при автоцикле):**  
`loop/runtime/epic/result.yaml` (или `program/`) — machine status.  
**Не** патчить `loop-state.yaml` вручную — runner `after` применяет transitions.

```yaml
version: 1
status: ok
verdict: null
step_id: sNN
artifact: null
role: BACK
mode: IMPLEMENT
notes: null
```

```bash
python3 .claude/hooks/loop_resolve.py result --template
python3 .claude/hooks/loop_resolve.py graph --check
```

Канон: `loop/README.md` · `.cursor/rules/shared/workflow-loop-state.mdc`  
`- **Следующий:**` = human hint (выровнять с tip / `loop-state.next`); машинный next — runner + `transitions.yaml`.

```markdown
## Handoff BACK IMPLEMENT T-xxx sNN

- **Сделано:** …
- **Артефакт:** [sNN-slug.yaml](back/implement/implement-<plan>/sNN-slug.yaml)
- **Файлы:** `path/…` (если code_changed)
- **Проверка:** pytest / verify PASS / result.yaml ok
- **Статус:** sNN completed; …
- **Следующий:** `<ROLE> <MODE>` @target — по tip `next_phase` / ledger (не выдумывать цепочку).
```

QA (обязателен всегда — pass и blocked). Роль: `BACK` | `FRONT` | `INTEG` — подставить в заголовок и пути.

```markdown
## Handoff BACK QA T-xxx <plan_id>

- **Предыдущий:** BACK QA — [qa-YYYYMMDD-<plan_id>](memory-bank/back/qa/<epic_id>/qa-….yaml) — pass|fail|blocked
- **Verdict:** pass | fail | blocked
- **Артефакт:** memory-bank/back/qa/<epic_id>/qa-YYYYMMDD-<plan_id>.yaml
- **Epic:** T-xxx / `<plan_id>` — что проверяли (шаги, сервисы)
- **code_changed:** no
```

Без эпика: путь плоско `memory-bank/back/qa/qa-….yaml`. Канон: @.cursor/rules/shared/epic-scoped-paths.mdc.

**pass** — добавить:
- **Следующий:** BACK REFLECT | BACK IMPLEMENT sNN+1 | ARCHIVE NOW
- **Кратко:** suite green; scope подтверждён
- **New chat:** yes → REFLECT или следующий IMPLEMENT

**fail | blocked** — добавить (обязательно):
- **Следующий:** `BACK BUGFIX` (первая строка Fix plan) → затем повторный `BACK QA`
- **Fix plan:** таблица из qa-артефакта `fix_plan[]` (минимум первая строка в Handoff):
  - `#1` `BACK BUGFIX <subject>` — files: `…` — verify: `…`
- **Epic QA (повтор):** `BACK QA <plan_id> — <предмет>`; scope: `s01–s18`; suite: `…`
- **Кратко:** N blockers; первая — QA-1 …
- **New chat:** yes → `BACK BUGFIX <subject #1>`

IMPLEMENT — последний шаг эпика (все строки decompose = `completed`):

```markdown
## Handoff BACK IMPLEMENT T-xxx sNN (epic complete)

- **Предыдущий:** [sNN slug](memory-bank/.../sNN-slug.yaml) — done; **эпик `<plan_id>` завершён**
- **Следующий:** `BACK QA` (обязательно перед REFLECT)
- **Epic QA:**
  - **Команда:** `BACK QA <plan_id> — <предмет из plan/decompose>`
  - **Эпик:** T-xxx / `<plan_id>`
  - **Scope:** все шаги implement (напр. s01–s18, compose, full suite) — AC из Handoff/suite, **не** полный plan в load_now
  - **Suite:** `.venv/bin/pytest` full; compose smoke если в scope шагов
  - **Артефакт:** `memory-bank/back/qa/qa-YYYYMMDD-<plan_id>.yaml`
- **Кратко:** implement done; QA эпика не выполнен / blocked — см. qa-артефакт
- **New chat:** yes → `BACK QA`
```

Аналогично для `FRONT IMPLEMENT` → `FRONT QA`; `INTEG IMPLEMENT` (все eNN done) → `INTEG QA`.

BUGFIX FINISH — обязательная рекомендация QA:

```markdown
## Handoff BACK BUGFIX <slug>

- **Предыдущий:** [bugfix-…](memory-bank/back/bugfix/bugfix-….md) — done
- **Источник QA:** [qa-…](memory-bank/back/qa/qa-….yaml) — issue QA-1, QA-2
- **Следующий:** `BACK QA <plan_id> — <предмет>` (повтор эпика; не REFLECT пока QA не pass)
- **Epic QA:** scope + suite из исходного qa §Epic QA
- **Осталось в Fix plan:** #2 `BACK BUGFIX …` (если были другие строки)
- **code_changed:** yes
- **New chat:** yes → `BACK QA`
```

Для idea: см. @.cursor/templates/idea-pipeline.md (Handoff в `idea-*.md` + activeContext).

## Сообщение пользователю (если New chat: yes)

**IMPLEMENT (следующий шаг):**
```
Открой новый чат для следующего шага.

Команда: BACK IMPLEMENT sNN+1 — <slug>

Старт:
1. memory-bank/activeContext.md → load_now + §Handoff
2. memory-bank/back/plan/decompose-<plan_id>/sNN-<slug>.yaml
```

**IMPLEMENT (эпик завершён → QA):**
```
Эпик <plan_id> (T-xxx) реализован. Следующий шаг — QA всей эпики.

Команда: BACK QA <plan_id> — <предмет проверки>

Что проверяем:
- эпик: T-xxx / <plan_id>, шаги s01–sNN
- suite: <команды из plan/handoff>
- compose/smoke: <если в scope>

Старт:
1. memory-bank/activeContext.md → §Handoff + load_now
2. memory-bank/back/implement/implement-<plan_id>/index.md
3. (опц.) последний qa-*.yaml при re-run — **не** plan-*.md
```

**QA blocked → BUGFIX:**
```
QA заблокирован (verdict: blocked). Следующий шаг — точечный BUGFIX.

Команда: BACK BUGFIX <subject из Fix plan #1>

Предмет: <одна фраза — что чиним>
Файлы: <paths из Fix plan>
Проверка: <verify из Fix plan>
Источник: qa-YYYYMMDD-<plan_id>.yaml → issue QA-1

Старт:
1. memory-bank/activeContext.md → load_now + §Handoff
2. memory-bank/back/qa/.../qa-*.yaml (fix_plan row) — **не** полный plan

После green → BACK QA <plan_id> — повтор эпики (new chat).
```

**BUGFIX done → повтор QA:**
```
BUGFIX завершён. Повторная валидация эпики.

Команда: BACK QA <plan_id> — <предмет>

Старт:
1. memory-bank/activeContext.md → §Handoff
2. memory-bank/back/qa/qa-YYYYMMDD-<plan_id>.yaml (предыдущий прогон)
3. memory-bank/back/bugfix/bugfix-YYYYMMDD-<slug>.md (что исправлено)
```

Для FRONT/INTEG — заменить префикс (`FRONT QA`, `INTEG BUGFIX`, пути `front/` / `integration/`).

Подставить реальные T-xxx, plan_id, subject, paths.
