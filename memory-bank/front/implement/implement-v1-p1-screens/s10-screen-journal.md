# [T-004 | s10 | screen-journal] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s10-screen-journal.md](../../plan/decompose-v1-p1-screens/s10-screen-journal.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `playwright-best-practices`
- `next-best-practices`
- `frontend-patterns`
- `frontend-design` *(visible UI — HARD)*
- `design-taste-frontend` *(visible UI — HARD)*
- `emil-design-eng` *(visible UI — HARD)*
- `impeccable` *(visible UI — HARD)*
- `high-end-visual-design` *(visible UI — HARD)*
- `ui-ux-pro-max` *(visible UI — HARD)*
- `verification-before-completion`

> Retro 2026-07-26: design stack зафиксирован как обязательный для visible UI (`workflow-implement` gate). В исходной сессии шага загружен частично/не загружен — следующие UI IMPLEMENT обязаны Read все 6 до кода.


## Сделано

- JournalPage: EventFilters + URL sync + virtual list (`@tanstack/react-virtual`) + sort (active-unacked top)
- Hooks: `useEventsInfinite` (cursor GET /api/events) + `useEventsRealtime` (WS prepend dedupe by id)
- ReconstructionBanner при `X-Events-Reconstruction`
- `trendsDeepLink(event)` → `/trends?tag&from&to&mode=quick` (±10 min)
- Print: PrintLayout provenance + `print-journal.css` (hide chrome, monochrome lamps)
- Footnote «Квитируется на панели АПС» — **нет** кнопки квитирования
- Route `(authenticated)/journal` → JournalPage (Suspense)

## Файлы

- `frontend/src/features/journal/JournalPage.tsx`
- `frontend/src/features/journal/useEventsInfinite.ts`
- `frontend/src/features/journal/useEventsRealtime.ts`
- `frontend/src/features/journal/ReconstructionBanner.tsx`
- `frontend/src/features/journal/journalFilters.ts`
- `frontend/src/features/journal/journalSort.ts`
- `frontend/src/features/journal/JournalPage.test.tsx`
- `frontend/src/lib/routing/trendsDeepLink.ts`
- `frontend/src/lib/routing/trendsDeepLink.test.ts`
- `frontend/src/styles/print-journal.css`
- `frontend/src/app/(authenticated)/journal/page.tsx`
- `frontend/e2e/specs/journal/no-ack-deeplink.spec.ts`
- dep: `@tanstack/react-virtual`

## Тесты

- cmd: `cd frontend && npm test -- src/lib/routing/trendsDeepLink.test.ts src/features/journal/JournalPage.test.tsx`
- итог: 7 passed (filter+URL, no ack, deep link window, reconstruction, sort)
- scenario: `npx playwright test e2e/specs/journal/no-ack-deeplink.spec.ts` → 1 passed
- Scenario E2E: `e2e/specs/journal/no-ack-deeplink.spec.ts` (AC-5-01/03/05 + banner)
- PW-03/04 full filter-print / trends chart → s16

## Integration check

- [x] GET `/api/events` ↔ `fetchEvents` / `useEventsInfinite` + MSW
- [x] Header `X-Events-Reconstruction` ↔ ReconstructionBanner (E2E: Access-Control-Expose-Headers)
- [x] WS `events` ↔ `useEventsRealtime` / `useWsChannel`
- [x] DS `EventFilters` / `EventRow` / `PrintLayout` / `StateShell`
- [x] `trendsDeepLink` ↔ `/trends?…&mode=quick`
- [x] `data-testid` journal-page, journal-filters, event-row, reconstruction-banner, aps-ack-footnote, print-layout
- [ ] Full PW-03/04 → s16
