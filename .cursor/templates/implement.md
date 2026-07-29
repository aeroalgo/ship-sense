# [T-xxx | slug] IMPLEMENT

**Дата:** YYYY-MM-DD  
**Уровень:** L1–L4  
**Статус:** in_progress | done

> **Epic (предпочтительно):** шаблон шага в папке — [.cursor/templates/implement/step.md](implement/step.md); hub — [.cursor/templates/implement/index.md](implement/index.md).  
> Путь BACK/FRONT: `memory-bank/<back|front>/implement/implement-<plan_id>/sNN-<slug>.md`  
> Путь INTEG: `memory-bank/integration/implement/implement-<plan_id>/eNN-<slug>.md` — [.cursor/templates/implement/integ-index.md](implement/integ-index.md) / [integ-step.md](implement/integ-step.md)  
> Legacy flat `implement-<task_id>.md` в корне `implement/` — только для одиночных задач / старых journey без decompose.

> **Skills (epic/decompose):** не дублировать — канон в linked `sNN` / `eNN`. Legacy flat без decompose: кратко перечисли Read skills.

## Сделано

- …

## Файлы

- `path/to/file.py`

## Тесты

- cmd: `pytest …`
- итог: N passed

## Integration check

- [ ] storage keys wired
- [ ] env vars in settings
- [ ] DB cols ↔ migration
- [ ] events ↔ handlers
