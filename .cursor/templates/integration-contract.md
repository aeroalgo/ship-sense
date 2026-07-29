# Contract: <domain-slug>
**Task ID:** <T-xxx>
**Status:** draft | active | done

## Entity
- **Model:** `app.<entity>.model.<Entity>`
- **Table:** `<table_name>`
- **Scope:** partner / public

## Endpoints
| Method | Path | Purpose | Default filters |
|--------|------|---------|-----------------|
| GET | `/api/v1/<resource>/list` | list + pagination | `{}` |

## UI FilterState
```typescript
interface <Domain>FilterState {
  // UI fields
}
```

## Filter key matrix
| UI field | List endpoint key | Param type | Facets endpoint | mapping_filters path |
|----------|-------------------|------------|-----------------|----------------------|
| | | `filters` \| `gt` \| `lt` \| `period` | | |

## QueryBuilder config
- **model:** `<Entity>`
- **period_mode:** `created_at`
- **mapping_filters:** @.agents/skills/query-builder/references/JOINS-AND-MAPPING.md
- **query params:** @.agents/skills/query-builder/references/QUERY-PARAMS.md

## Query params (PaginateQueryParams)
- `filters`: JSON dict, values = string[] — enum, multiselect, `relation__column`
- `gt` / `lt` / `eq`: JSON dict — числовые границы (`price__gte`, `price__lte`)
- `period`: `"YYYY-MM-DD:YYYY-MM-DD"` on `<period_field>`
- `page`, `size`, `search`, `ascending`, `descending`

## Response
- `data.items[]`, `data.total`, `data.page`, `data.size`, `data.pages`
- `meta.read_table_mapping[]` — if table UI

## BACK files
- `app/<entity>/schema.py`
- `api/v1/endpoints/<entity>.py`
- `tests/api/test_<entity>.py`

## FRONT files
- `frontend/src/lib/api/<domain>.ts`
- `frontend/src/lib/filters/<domain>-filters.ts`
- `frontend/src/lib/query-keys/<domain>.ts`
- `frontend/src/hooks/use-<domain>.ts`

## Consumers
- `frontend/src/app/...`
- `frontend/src/components/...`

## §0.11 pairs
| Back | Front | BACK implement ref | FRONT implement ref |
|------|-------|--------------------|---------------------|
| | | | |

> Пары только из implement §Файлы + grep verify. Plan/decompose shards — не источник.
