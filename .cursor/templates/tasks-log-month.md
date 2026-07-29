# Delivery log — шаблон месяца

Скопировать в `memory-bank/tasks/log/YYYY-MM.md` при первом FINISH месяца.

```markdown
# Delivery log — YYYY-MM

Сквозная хронология эпиков. **Append на каждом FINISH** (обязательно). Не в `load_now`.

## Timeline

| Дата | Task | Событие | Артефакт |
|------|------|---------|----------|
| YYYY-MM-DD | T-xxx | BACK IMPLEMENT sNN | [sNN-slug.md](back/implement/.../sNN-slug.md) |
```

На FINISH также обновить §Последние события в `tasks.md` (последние 5 строк).
