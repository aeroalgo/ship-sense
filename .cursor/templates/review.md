# [T-xxx | slug] REVIEW

**Дата:** YYYY-MM-DD  
**Reviewer:** BACK QA  
**Verdict:** pass | fail | blocked

## Scope

- task: T-xxx
- files: …

## Checks

- [ ] tests green
- [ ] integration rule (§0.11)
- [ ] no phantom refs
- [ ] edge cases covered

## Issues

| ID | sev | file | msg |
|----|-----|------|-----|
| R-1 | … | … | … |

## Blockers

- …

## Fix plan (обязательно при verdict `fail` | `blocked`)

Одна строка = один заход BUGFIX. Сортировка: blocker → high → medium → low. `out_of_scope` — отдельно, без команды BUGFIX.

| # | issue | command | subject | scope / files | verify |
|---|-------|---------|---------|---------------|--------|
| 1 | QA-1 | `BACK BUGFIX` | slow MQTT E2E не terminal в QA budget | `apps/edge/collector/tests/integration/test_mqtt_e2e.py`, `conftest.py` | `.venv/bin/pytest … -m slow` terminal green |
| 2 | QA-2 | `BACK BUGFIX` | compose runtime ModbusException flood | `connector.py`, `sources.dev.yaml` | `docker compose logs collector` без ModbusException |

**Правила:**
- `command` — полная role-команда: `BACK BUGFIX` | `FRONT BUGFIX` | `INTEG BUGFIX`
- `subject` — одна фраза для чата: `BACK BUGFIX <subject>` (копируется в bugfix slug)
- Независимые issue → отдельные строки и отдельные bugfix-сессии (не смешивать в одном BUGFIX)
- Связанные issue одной root cause → одна строка, перечислить issue IDs
- После всех BUGFIX → повторный QA той же эпики (см. §Epic QA ниже)

## Epic QA (для повторного прогона после BUGFIX или IMPLEMENT)

```markdown
**Epic QA:** `BACK QA` | `FRONT QA` | `INTEG QA`
**Эпик:** T-xxx / `<plan_id>` (напр. `v1-p1-storage`)
**Предмет:** что проверяем одной фразой
**Scope:** шаги s01–s18 | e01–e05; ключевые пути/сервисы
**Suite:** команды прогона (`.venv/bin/pytest`, vitest, playwright, compose smoke)
**Артефакт:** memory-bank/{back|front|integration}/qa/qa-YYYYMMDD-<plan_id>.md
**Старт:** activeContext → load_now + последний qa-артефакт + implement index эпика
```
