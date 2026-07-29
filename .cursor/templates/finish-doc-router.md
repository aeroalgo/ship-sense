# FINISH — doc-router update

**Task:** T-xxx  
**Command:** BACK IMPLEMENT | QA | REFLECT | ARCHIVE | PLAN | VAN | INTEG …

Канон заполнения `activeContext.md` (единственный Handoff). Rules (`finish-doc-router.mdc`) дают **когда** и **By command** / graphify / Forbidden — не дублировать здесь.

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

## Shard checkbox / implement

- [x] AC/checklist в `implement/sNN` (секции Сделано, Файлы, Тесты) — **без** `## Handoff`
- [ ] **ЗАПРЕЩЕНО** `## Handoff` / `## Следующий шаг` в implement

## Decompose index (если шаг из `decompose-*/`)

- [ ] `status: done` в `decompose-*/index.md`
- [ ] `[x]` в Summary-чеклисте  
  (не через `tasks.md`)

## Handoff (только `activeContext.md`)

Единый каркас — **перезаписать**, не копить старые блоки:

```markdown
## Handoff BACK IMPLEMENT T-xxx sNN

- **Предыдущий:** [sNN slug](memory-bank/.../implement/.../sNN-slug.md) — done
- **Следующий:** [sNN+1 slug](memory-bank/.../decompose-.../sNN+1-slug.md)
- **Кратко:** …
- **New chat:** yes | no (reason)
```

Для idea: см. @.cursor/templates/idea-pipeline.md (Handoff в `idea-*.md` + activeContext).

## Сообщение пользователю (если New chat: yes)

```
Открой новый чат для следующего шага (экономия контекста).

Команда: BACK IMPLEMENT | BACK QA |

Старт:
1. memory-bank/activeContext.md → load_now + §Handoff
2. memory-bank/back/plan/decompose-<plan_id>/sNN-<slug>.md
```

Подставить реальные команду и пути.
