# Шаг r03: Move `apps/edge/semantic` → `app.semantic`
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** yes  
**Priority:** High  
**Depends:** r01 (рекомендация: после r02)  
**code_changed:** yes  
**AC:** plan §5.3 AC C

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

---

## Цель
Пакет semantic (models/loader/engine/quarantine) переезжает в `apps/api/app/semantic/`. Все импорты `apps.edge.semantic` → `app.semantic`. Старый каталог удалён (без долгого shim).

## Контекст
- **Consumes:** r01; существующий `apps/edge/semantic/{models,loader,engine,quarantine}.py`; потребители storage/writer/tests.
- **Produces:** `app.semantic.*`; нулевой `apps.edge.semantic` в `*.py` (кроме archive memory-bank).

## Файлы
- `apps/api/app/semantic/__init__.py` (Создание)
- `apps/api/app/semantic/models.py` (Создание/перенос)
- `apps/api/app/semantic/loader.py` (Создание/перенос)
- `apps/api/app/semantic/engine.py` (Создание/перенос)
- `apps/api/app/semantic/quarantine.py` (Создание/перенос)
- `apps/edge/semantic/` (Удаление) — весь пакет
- `apps/edge/storage/__main__.py` / writer quarantine hooks (Модификация) — `app.semantic`
- тесты semantic/storage quarantine (Модификация) — импорты

## Интерфейсы (lean — без кода)
- models: AssetNode, TagMeta, SemanticPack, QuarantineEntry/Report, VesselDef, SourceDef, … — **имена as-is**, behavior freeze
- class: `SemanticEngine` — публичные методы as-is
- loader: `SemanticPackError` + load entrypoints as-is
- rule: `app.semantic.models` без fastapi imports
- rule: нет dual package `apps.edge.semantic` + `app.semantic`

## TDD (красная → зелёная)
1. **Before:** semantic-related + `tests/storage/test_quarantine.py` (и смежные) green.
2. **Refactor:** move + rewire + delete old.
3. **After:** те же тесты green; import smoke `app.semantic`.

## Подробный процесс выполнения
1. Перенести файлы в `apps/api/app/semantic/`.
2. Заменить импорты во всех `*.py`.
3. Удалить `apps/edge/semantic/`.
4. Прогнать quarantine + semantic unit tests.
5. Не менять YAML schema / quarantine semantics.

## Чекпоинт верификации
- `rg "apps\\.edge\\.semantic" --glob '*.py'` = 0 (кроме archive)
- `app.semantic.models` без fastapi
- targeted pytest green
- `.venv/bin/graphify update .` на FINISH
