# plan-INTEG-<task_id>

**Дата:** YYYY-MM-DD  
**Режим:** INTEG PLAN  
**Scope:** portal | journey | section  
**Домен/slug:** <portal-journey-slug>  
**Статус:** draft | active | done  
**Gap ref (опционально):** [gap-YYYYMMDD-<slug>.md](../gap/gap-YYYYMMDD-<slug>.md)

→ [decompose-<plan_id>/index.md](decompose-<plan_id>/index.md) — **после DECOMPOSE:** единственный трекер status `eNN` (не дублировать `- [ ] e01…` в этом plan)

## Суть

Master-план wire **всего портала** (или указанного section): каждый route, UI-элемент, API-вызов к БД. Движение — по элементам страниц, не по слоям BACK/FRONT.

## Element registry (as-built)

> Источник: routes `frontend/src/app/**` + components + `back/implement/` + `front/implement/` — **не** gap/, contracts/, plan/decompose shards.
> После таблицы — **обязательны** секции `## Element eNN — …` для каждого P0/P1 (не ограничиваться одной таблицей).
> Registry + per-element §§ = **стратегия/as-built**, не runtime-трекер done/pending.

| route | UI element (component) | data need | API today | BACK implement | FRONT implement | priority |
|-------|------------------------|-----------|-----------|----------------|-----------------|----------|
| `/` | `Hero` — поиск города | redirect city | none / mock | — | implement-… | P0 |
| `/catalog` | `FilterBar` + list | activities list | ❌ mock | pending | implement-… | P0 |

**Legend API today:** ✅ live | ❌ missing | ⚠️ mock fallback | — static

## Element e01 — <title> (повторить на каждый P0/P1)

### §UI
- route, component path(s)

### §Data need
- …

### §API today
- ✅ / ⚠️ / ❌ + real path

### §Contract outline
```
METHOD /path
request…
response…
```

### §BACK / §FRONT wire
- …

### §Verify
- §0.11 pair + test cmd


## API inventory

| Method | Path | DB tables | Consumer element(s) | Status |
|--------|------|-----------|---------------------|--------|
| GET | `/api/v1/activities` | activity, city | FilterBar, ActivityShowcase | ❌ |

## User journeys (E2E)

| ID | Persona | Path | Elements touched |
|----|---------|------|------------------|
| J1 | Guest | Home → Catalog → Activity | e01, e04, e06 |
| J2 | Client | Slot → Checkout → Dashboard | e07, e10, e11 |

## Rollout (by UI element, not by layer)

> Порядок фаз — стратегия. **Не** ставить `- [ ]` / `done` здесь. Статус элементов → `decompose/index.md` после DECOMPOSE.

**Фаза 0 — Discovery (guest funnel)**
1. e04 catalog list + filters
2. e06 activity detail + e07 booking widget

**Фаза 1 — Transaction**
3. e09 auth gate
4. e10 checkout

**Фаза 2 — Portals**
5. e11 client bookings
6. e16 provider scheduler …

## Test matrix

| Journey | BACK pytest | FRONT vitest | Wire / E2E |
|---------|-------------|--------------|------------|
| J1 | test_activities | catalog-filters.test | Playwright catalog |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mock in ActivityShowcase | false green home | e03 wire first |

## Handoff

- **Done:** …
- **Files:** этот plan
- **Next:** INTEG DECOMPOSE (element-first `eNN-*.md`)
- **New chat:** yes
