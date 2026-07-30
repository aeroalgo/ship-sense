# Шаг r04: Import-graph audit tests + README
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** yes  
**Priority:** High  
**Depends:** r02, r03  
**code_changed:** yes  
**AC:** plan §5.6 Фаза F

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

---

## Цель
Закрепить Shared Kernel правилами автотестами и обновить collector README: канон = `app.*`, collector = Raw*+health.

## Контекст
- **Consumes:** r02+r03 (модели и semantic на местах); plan §3.1 import rules; C-01 / I1 mirror.
- **Produces:** три audit-теста + README; regression harness для ownership.

## Файлы
- `apps/api/tests/unit/test_domain_no_fastapi.py` (Создание) — AST/importlib: telemetry/events/semantic models без fastapi
- `tests/storage/test_no_collector_domain_canonical.py` (Создание) — storage не импортирует collector canonical
- `apps/edge/collector/tests/unit/test_plugins_no_app_canonical.py` (Создание) — `plugins/*` не импортируют `app.telemetry`/`app.events`
- `apps/edge/collector/README.md` (Модификация) — § канон / ownership

## Интерфейсы (lean — без кода)
- test helpers: scan modules under path; assert forbidden import names
- allowed: collector core/sinks → `app.telemetry`/`app.events` (не plugins transport)
- forbidden: models → fastapi; storage → `collector.domain` canonical; plugins → `app.telemetry`/`app.events`

## TDD (красная → зелёная)
1. **Тест:** написать audit tests (могут FAIL если r02/r03 неполны — тогда сначала добить ownership).
2. **Запуск:** targeted audit FAIL→fix imports→PASS.
3. **README:** обновить без смены runtime.
4. **Smoke:** unit scope plan §11 r04.

## Подробный процесс выполнения
1. Реализовать три audit-теста по plan §5.6.
2. Починить любые нарушения ownership (минимально; не трогать behavior).
3. Обновить README collector.
4. Прогнать audit + короткий smoke unit.

## Чекпоинт верификации
- Три audit-теста green
- README отражает `app.*` ownership
- `.venv/bin/graphify update .` на FINISH
