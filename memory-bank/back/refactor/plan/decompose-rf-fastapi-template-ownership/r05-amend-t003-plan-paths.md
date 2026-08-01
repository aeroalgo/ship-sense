# Шаг r05: Amend T-003 plan + decompose paths → `apps/api`
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** no  
**Priority:** Critical (docs / delivery unblock)  
**Depends:** r01 (пути существуют; финальные пути = skill)  
**code_changed:** no  
**AC:** plan §5.5 AC E

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.  
> **Docs-only:** только `memory-bank/**`; без правок runtime-кода.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

---

## Цель
Feature-план T-003 и все `decompose-v1-p1-api/s01–s10` описывают `apps/api/app/...` (fastapi-templates), не `apps/edge/api`. Снять path-блокер для будущего `BACK IMPLEMENT s01`.

## Контекст
- **Consumes:** r01 дерево; rf-plan §2.1; текущие [plan-v1-p1-api.md](../../../plan/plan-v1-p1-api.md) + [decompose-v1-p1-api](../../../plan/decompose-v1-p1-api/index.md).
- **Produces:** обновлённые plan §13 + sNN file lists; note на RF-01; явная ссылка на skill.

## Файлы
- `memory-bank/back/plan/plan-v1-p1-api.md` (Модификация) — §13 file tree, mermaid/package refs
- `memory-bank/back/plan/decompose-v1-p1-api/index.md` (Модификация) — ссылка на RF-01; unblock note после r05
- `memory-bank/back/plan/decompose-v1-p1-api/s01-scaffold.yaml` (Модификация) — files → `apps/api/app/...`; `code_surface`/skills: **fastapi-templates**
- `memory-bank/back/plan/decompose-v1-p1-api/s02-*.md` … `s10-*.md` (Модификация) — routers→`app/api/v1/endpoints`, services→`app/<feature>/service.py`, schemas→`app/<feature>/schemas.py`
- `memory-bank/activeContext.md` / `tasks.md` (Модификация на FINISH r05) — T-003 path unblock если r01+r02 тоже done

## Интерфейсы (lean — без кода)
- n/a (документы)
- правило: в целевом дереве plan **нет** `apps/edge/api/` (historical notes только в archive)
- s01 lists: `apps/api/app/main.py`, `app/api/v1/...`, `app/core/...`
- явная строка: структура = fastapi-templates SKILL

## TDD (нет)
- **Причина:** docs-only amend memory-bank; нет runtime regression в этом rNN.
- **Верификация:** `rg "apps/edge/api" memory-bank/back/plan/plan-v1-p1-api.md memory-bank/back/plan/decompose-v1-p1-api` — целевых путей = 0; spot-check s01–s10 paths.

## Подробный процесс выполнения
1. Заменить §13 plan на дерево rf-plan §2.1 (адаптировать под T-003 endpoints).
2. Пройти s01–s10: каждый path `apps/edge/api/...` → skill path.
3. s01: добавить/подтвердить Impl skill `fastapi-templates`.
4. index: ссылка на `rf-fastapi-template-ownership`; снять «blocked by path» если r01+r02 completed.
5. Не менять REST/WS контракт T-003 (только package paths).

## Чекпоинт верификации
- AC E чеклист plan §5.5
- T-003 IMPLEMENT s01 разблокирован **только если** также r01+r02 done
