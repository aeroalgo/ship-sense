# FINISH — doc-router update

**Task:** T-xxx  
**Command:** BACK IMPLEMENT | QA | REFLECT | ARCHIVE | PLAN | VAN | INTEG …

Канон заполнения `activeContext.md`: **ровно один** `## Handoff` — **перезапись**, не append.  
**FAIL:** два и более `## Handoff` в файле. История шагов → `tasks/log/` + implement/qa/bugfix shards, не сюда.  
Rules (`finish-doc-router.mdc`) дают **когда** и **By command** / graphify / Forbidden — не дублировать здесь.

## Перенести в done

- [ ] path/to/completed-shard-or-artifact.md  
  → из `load_now` в `done — do NOT load`

## Новый load_now (max 3)

1. next step shard (`decompose-*/sNN|eNN-*.md`) — **путь к shard-файлу**, не к index
2. plan/AC shard если нужен AC — **INTEG:** implement artifact или integration plan (не back/front decompose как единственный вход)
3. `decompose-*/index.md` если нужен обзор очереди шагов

## load_if_needed (trim)

- … — только shards, релевантные **следующему** шагу

## activeContext §Сейчас / §Следующий шаг

1. … — канон «где стоим»; без `focus/`

## tasks.md Index

- [ ] обновить колонки **Step**, **Status** и **Progress** для T-xxx
- [ ] **обязательно:** append строка в `tasks/log/YYYY-MM.md` (§Delivery log)

## Delivery log (обязательно)

Файл: `memory-bank/tasks/log/YYYY-MM.md` — append **одна строка** в таблицу §Timeline:

```markdown
| YYYY-MM-DD | T-xxx | BACK IMPLEMENT sNN | [sNN-slug.md](back/implement/.../sNN-slug.md) |
```

Также обновить §Последние события в `tasks.md` (последние 5 строк, без деталей).

**Когда:** FINISH с завершённым atomic subtask (IMPLEMENT sNN, PLAN, DECOMPOSE, CREATIVE, QA, BUGFIX, TASK).  
**Пропуск:** checkbox внутри того же шага; typo-only правки.

## Shard checkbox / implement (ORDER — до decompose completed)

- [ ] **Файл существует:** `memory-bank/{back|front|integration}/implement/implement-<plan>/sNN|eNN-<slug>.md` (не stub)
- [x] Секции Реализация (Сделано/Файлы) · Верификация/Тесты · Статус=`completed` — **без** `## Handoff` внутри step
- [ ] **ЗАПРЕЩЕНО** `## Handoff` / `## Следующий шаг` в implement step
- [ ] **## Handoff** этого `sNN|eNN` уже в `activeContext.md` (шаг ниже) — **до** галки decompose

## Decompose index (если шаг из `decompose-*/`) — только после step + Handoff

- [ ] `status: completed` / `done` в `decompose-*/index.md` (**после** step-файла + Handoff)
- [ ] `[x]` в Summary-чеклисте  
  (не через `tasks.md`)
- [ ] `implement/index.md` — ссылки only, **без** `done`/`completed`/status suffix

## Handoff (только `activeContext.md`)

**HARD — ONE block:** в файле после FINISH должен остаться **единственный** заголовок `## Handoff …`.  
Действие: **replace** всего предыдущего блока (или удалить все старые `## Handoff` и записать один новый).  
**FORBIDDEN:** prepend/append второго Handoff; стопка «s03, s04, QA, REFLECT»; дублировать Handoff в implement step.  
Порядок секций: `## load_now` → **один** `## Handoff …` → `## done — do NOT load`.  
Писать **до** sync decompose/`load_now`:

```markdown
## Handoff BACK IMPLEMENT T-xxx sNN

- **Предыдущий:** [sNN slug](memory-bank/.../implement/.../sNN-slug.md) — done
- **Следующий:** [sNN+1 slug](memory-bank/.../decompose-.../sNN+1-slug.md)
- **Кратко:** …
- **New chat:** yes | no (reason)
```

QA (обязателен всегда — pass и blocked). Роль: `BACK` | `FRONT` | `INTEG` — подставить в заголовок и пути.

```markdown
## Handoff BACK QA T-xxx <plan_id>

- **Предыдущий:** BACK QA — [qa-YYYYMMDD-<plan_id>](memory-bank/back/qa/<epic_id>/qa-….md) — pass|fail|blocked
- **Verdict:** pass | fail | blocked
- **Артефакт:** memory-bank/back/qa/<epic_id>/qa-YYYYMMDD-<plan_id>.md
- **Epic:** T-xxx / `<plan_id>` — что проверяли (шаги, сервисы)
- **code_changed:** no
```

Без эпика: путь плоско `memory-bank/back/qa/qa-….md`. Канон: @.cursor/rules/shared/epic-scoped-paths.mdc.

**pass** — добавить:
- **Следующий:** BACK REFLECT | BACK IMPLEMENT sNN+1 | ARCHIVE NOW
- **Кратко:** suite green; scope подтверждён
- **New chat:** yes → REFLECT или следующий IMPLEMENT

**fail | blocked** — добавить (обязательно):
- **Следующий:** `BACK BUGFIX` (первая строка Fix plan) → затем повторный `BACK QA`
- **Fix plan:** таблица из qa-артефакта §Fix plan (минимум первая строка в Handoff):
  - `#1` `BACK BUGFIX <subject>` — files: `…` — verify: `…`
- **Epic QA (повтор):** `BACK QA <plan_id> — <предмет>`; scope: `s01–s18`; suite: `…`
- **Кратко:** N blockers; первая — QA-1 …
- **New chat:** yes → `BACK BUGFIX <subject #1>`

IMPLEMENT — последний шаг эпика (все строки decompose = `completed`):

```markdown
## Handoff BACK IMPLEMENT T-xxx sNN (epic complete)

- **Предыдущий:** [sNN slug](memory-bank/.../sNN-slug.md) — done; **эпик `<plan_id>` завершён**
- **Следующий:** `BACK QA` (обязательно перед REFLECT)
- **Epic QA:**
  - **Команда:** `BACK QA <plan_id> — <предмет из plan/decompose>`
  - **Эпик:** T-xxx / `<plan_id>`
  - **Scope:** все шаги implement + plan AC (напр. s01–s18, compose, full suite)
  - **Suite:** `.venv/bin/pytest` full; compose smoke если в plan
  - **Артефакт:** `memory-bank/back/qa/qa-YYYYMMDD-<plan_id>.md`
- **Кратко:** implement done; QA эпика не выполнен / blocked — см. qa-артефакт
- **New chat:** yes → `BACK QA`
```

Аналогично для `FRONT IMPLEMENT` → `FRONT QA`; `INTEG IMPLEMENT` (все eNN done) → `INTEG QA`.

BUGFIX FINISH — обязательная рекомендация QA:

```markdown
## Handoff BACK BUGFIX <slug>

- **Предыдущий:** [bugfix-…](memory-bank/back/bugfix/bugfix-….md) — done
- **Источник QA:** [qa-…](memory-bank/back/qa/qa-….md) — issue QA-1, QA-2
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
2. memory-bank/back/plan/decompose-<plan_id>/sNN-<slug>.md
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
3. memory-bank/back/plan/plan-<plan_id>.md (AC)
```

**QA blocked → BUGFIX:**
```
QA заблокирован (verdict: blocked). Следующий шаг — точечный BUGFIX.

Команда: BACK BUGFIX <subject из Fix plan #1>

Предмет: <одна фраза — что чиним>
Файлы: <paths из Fix plan>
Проверка: <verify из Fix plan>
Источник: qa-YYYYMMDD-<plan_id>.md → issue QA-1

После green → BACK QA <plan_id> — повтор эпики (new chat).
```

**BUGFIX done → повтор QA:**
```
BUGFIX завершён. Повторная валидация эпики.

Команда: BACK QA <plan_id> — <предмет>

Старт:
1. memory-bank/activeContext.md → §Handoff
2. memory-bank/back/qa/qa-YYYYMMDD-<plan_id>.md (предыдущий прогон)
3. memory-bank/back/bugfix/bugfix-YYYYMMDD-<slug>.md (что исправлено)
```

Для FRONT/INTEG — заменить префикс (`FRONT QA`, `INTEG BUGFIX`, пути `front/` / `integration/`).

Подставить реальные T-xxx, plan_id, subject, paths.
