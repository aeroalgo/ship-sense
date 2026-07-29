# [T-004 | s12 | screen-trends] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s12-screen-trends.md](../../plan/decompose-v1-p1-screens/s12-screen-trends.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `playwright-best-practices`
- `next-best-practices`
- `vercel-react-best-practices`
- `vercel-composition-patterns`
- `frontend-patterns`
- `frontend-design` *(visible UI — HARD)*
- `design-taste-frontend` *(visible UI — HARD)*
- `emil-design-eng` *(visible UI — HARD)*
- `impeccable` *(visible UI — HARD)*
- `high-end-visual-design` *(visible UI — HARD)*
- `ui-ux-pro-max` *(visible UI — HARD)*
- `verification-before-completion`

**Design read:** ship-bridge HMI trends tool for watch mechanics — ISA-101 dense ops chrome, tokens-only DS0; signature = mode strip + TagPicker + honest chart (gaps/setpoints/markers); not bare Grafana.

## Сделано

- TrendsPage: mode quick/extended, TagPicker, presets 1h/8h/24h/7d, Live toggle (extended)
- Hooks: useSeries (aggregate if multi), useSetpoints→bands, useEventMarkers, useTrendRealtime (WS tail quick)
- Deep link searchParams: tag/from/to/mode; journalFromMarker → `/journal?event_name&highlight&from&to`
- 413 → «Сократите период (max 90 дней)»; empty → «У тега нет данных за период»
- Route `(authenticated)/trends` → Suspense + TrendsPage

## Файлы

- `frontend/src/features/trends/TrendsPage.tsx`
- `frontend/src/features/trends/TrendsPage.test.tsx`
- `frontend/src/features/trends/trendsParams.ts`
- `frontend/src/features/trends/journalFromMarker.ts`
- `frontend/src/features/trends/useSeries.ts`
- `frontend/src/features/trends/useSetpoints.ts`
- `frontend/src/features/trends/useEventMarkers.ts`
- `frontend/src/features/trends/useTrendRealtime.ts`
- `frontend/src/app/(authenticated)/trends/page.tsx`
- `frontend/e2e/specs/trends/deep-link.spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/features/trends/TrendsPage.test.tsx`
- итог: 3 passed (deep link; marker→journal; empty copy)
- Scenario E2E: `npx playwright test e2e/specs/trends/deep-link.spec.ts` — 1 passed

## Integration check

- [x] searchParams ↔ trendsDeepLink (tag/from/to/mode=quick)
- [x] GET /api/series · /api/series/aggregate · /api/setpoints · /api/events · /api/assets/tree
- [x] WS values tail via useWsChannel (quick on; extended Live toggle)
- [x] marker → journal intent (event_name + highlight + window)
- [x] 413 copy PERIOD_TOO_LONG_COPY
- [ ] Full PW-04 suite polish → s16
