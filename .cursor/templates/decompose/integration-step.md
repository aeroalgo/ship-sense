# eNN: <UI element title>
**Plan ID:** <plan_id>
**Element ID:** eNN
**Next Phase:** INTEG IMPLEMENT

> **Policy:** статус элемента здесь не хранить. Статус живёт только в `implement/eNN-*.md` и `decompose/index.md`.

## §UI
- **Route:** `/catalog`
- **Component(s):** `frontend/src/components/catalog/filter-bar.tsx`, `frontend/src/app/catalog/page.tsx`
- **User sees:** фильтры города/сложности, список карточек активностей

## §Data need
- Список активностей из БД с фильтрами city, difficulty, period, search

## §API today
| Status | Detail |
|--------|--------|
| ❌ / ⚠️ / ✅ | endpoint exists? mock in component? |

## §Contract (lean — без кода)

Только якоря wire. **Запрещено:** полные TypeScript/Pydantic блоки, готовые тела handlers, copy-paste response schemas.

- **Method/path:** `GET /api/v1/activities`
- **Query keys:** `page`, `size`, `filters` (JSON), `search`
- **Filter map:** `city__slug` → filters JSON; `period` → `YYYY-MM-DD:YYYY-MM-DD`
- **Response shape:** `{ data[], meta: { total, page, size } }` — поля item: как `ActivityRead` в plan / соседнем endpoint
- **Front client:** `catalog-api.ts` → `fetchActivities` (сигнатура словами, без кода)

Детали типов и реализацию пишет INTEG IMPLEMENT по паттерну и plan.

## §DB
- `core.activity`, join `core.city` on slug

## §BACK
- [ ] migration / schema if missing
- [ ] `api/v1/endpoints/activities.py` + mapping_filters
- [ ] `tests/api/test_activities.py`

## §FRONT
- [ ] `frontend/src/lib/catalog-api.ts` — fetch по §Contract
- [ ] `frontend/src/lib/filters/catalog-filters.ts`
- [ ] wire `FilterBar` + page — убрать mock
- [ ] vitest: filter serialization

## §0.11
| Back | Front |
|------|-------|
| `api/v1/endpoints/activities.py` GET list | `catalog-api.ts` fetchActivities |

## §Verify
- `grep -r "/activities" frontend/src api/v1/`
- `pytest tests/api/test_activities.py`
- `npm test -- catalog`
- Browser: `/catalog?city=sochi` shows live data

## TDD
1. Red: pytest/vitest по §Contract
2. Green: BACK then FRONT
3. Wire + §Verify

## Checkpoint
- curl live list returns 200 + items
- UI card shows DB title, not mock string
