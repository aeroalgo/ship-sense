# BACK REFACTOR — r05 amend T-003 plan paths

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r05`
- **Дата:** 2026-07-30
- **Behavior freeze:** REST/WS контракт T-003, package ownership и runtime-код не меняются.
- **Scope:** docs-only; пути T-003 и decompose приведены к `apps/api/app/...` по fastapi-templates.

## Реализация / Файлы

- Подтверждён `memory-bank/back/plan/plan-v1-p1-api.md`: §2/§4/§13 используют `apps/api`, `app.*` и `app/api/v1/...`.
- Подтверждён `memory-bank/back/plan/decompose-v1-p1-api/`: s01–s10 используют `apps/api/app/...`, `apps/api/tests/...` и fastapi-templates.
- Сохранены только исторические упоминания `apps/edge/api` в notes/checklists; целевых file paths с legacy-деревом нет.
- Обновлены refactor/decompose/task handoff-артефакты: r05 закрыт, следующим остаётся r06.

## Верификация / Тесты

- `rg -n "apps/edge/api" memory-bank/back/plan/plan-v1-p1-api.md memory-bank/back/plan/decompose-v1-p1-api` → только 3 явных historical/verification notes, не целевые пути.
- Spot-check s01–s10: routers находятся в `apps/api/app/api/v1/endpoints`, feature services/schemas — в `apps/api/app/<feature>/`, tests — в `apps/api/tests/`.
- Runtime-тесты не запускались: r05 docs-only, `code_changed: no`.
- Behavior freeze подтверждён: REST/WS маршруты, payloads и runtime-код не изменялись.

## Статус

`completed`
