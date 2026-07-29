# [T-004 | s13 | screen-watch] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s13-screen-watch.md](../../plan/decompose-v1-p1-screens/s13-screen-watch.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `playwright-best-practices`
- `playwright-generate-test`
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

**Design read:** ship-bridge HMI watch handover brief (ISA-101) — verdict strip + protections never-collapse; not SaaS digest.

## Сделано

- WatchPage UI-A: handoff banner 60s, WatchVerdict, protections (collapsible=false), alarms DebounceGroupRow, drifts stub, DataQualityPanel, print
- debounce.ts: re-export CR-UI-04 + splitWatchEvents / period / verdict conflict
- useWatchReport: GET /api/reports/watch + events (highlights else /api/events)
- Route `(authenticated)/watch` → Suspense + WatchPage
- CTAs: `/journal?severity=alarm&active=1`, `/overview`

## Файлы

- `frontend/src/features/watch/WatchPage.tsx`
- `frontend/src/features/watch/WatchPage.test.tsx`
- `frontend/src/features/watch/useWatchReport.ts`
- `frontend/src/features/watch/DebounceGroupRow.tsx`
- `frontend/src/features/watch/DataQualityPanel.tsx`
- `frontend/src/features/watch/debounce.ts`
- `frontend/src/features/watch/debounce.test.ts`
- `frontend/src/app/(authenticated)/watch/page.tsx`
- `frontend/e2e/specs/watch/watch-compression.spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/features/watch/debounce.test.ts src/features/watch/WatchPage.test.tsx`
- итог: 8 passed (debounce 5 + page 3)
- Scenario E2E: `npx playwright test e2e/specs/watch/watch-compression.spec.ts` — 1 passed

## Integration check

- [x] GET /api/reports/watch ↔ fetchWatchReport ↔ queryKeys.watchReport
- [x] GET /api/events ↔ fetchEvents (fallback when highlights[])
- [x] watch-compression-spec constants ↔ features/watch/debounce
- [x] DS WatchVerdict / WatchSection / PrintLayout / Lamp
- [ ] Full PW-05 / PW-10 polish → s16; handoff UX polish → s14
