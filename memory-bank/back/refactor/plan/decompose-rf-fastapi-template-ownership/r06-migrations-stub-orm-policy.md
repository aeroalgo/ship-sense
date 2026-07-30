# Шаг r06: Migrations stub + ORM stays in storage
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** no  
**Priority:** Medium  
**Depends:** r01  
**code_changed:** yes/no (stub files only; ORM **не** переносить)  
**AC:** plan §5.4 policy locked

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

---

## Цель
Зафиксировать ORM policy фазы 1: SQLAlchemy таблицы остаются в `apps/edge/storage/schemas.py`. Опционально — пустой каркас `apps/api/migrations/` (env stub) **без** переноса Alembic storage. Документировать non-goal в README api.

## Контекст
- **Consumes:** r01; plan §5.4; writer = единственный writer архива.
- **Produces:** policy в README/`apps/api`; опц. empty migrations scaffold; **нет** двойного DeclarativeBase metadata.

## Файлы
- `apps/api/README.md` (Модификация) — ORM/migrations policy § фаза 1
- `apps/api/migrations/env.py` (Создание, опц.) — stub «not owner of DDL yet»
- `apps/api/migrations/versions/.gitkeep` (Создание, опц.)
- `apps/edge/storage/schemas.py` — **не трогать** схему

## Интерфейсы (lean — без кода)
- n/a runtime API
- policy: API читает через repos; может импортировать ORM из `apps.edge.storage.schemas` до follow-up
- forbid: перенос Alembic storage → api в этом эпике без отдельного AC

## TDD (нет)
- **Причина:** policy + optional empty scaffold; нет бизнес-логики.
- **Верификация:** schema storage неизменна; README содержит policy; если stub создан — не подключён как active migrate path writer.

## Подробный процесс выполнения
1. Записать ORM policy в `apps/api/README.md`.
2. Создать пустой migrations каркас **или** явно отложить с note в README (оба OK per plan).
3. Не переносить tables/Base.
4. Не менять writer migrate entrypoint.

## Чекпоинт верификации
- `apps/edge/storage/schemas.py` без DDL move
- Policy видима в api README
- Нет второго active Alembic chain для той же metadata
