# [T-004 | s09 | screen-overview] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s09-screen-overview.md](../../plan/decompose-v1-p1-screens/s09-screen-overview.md)
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

- OverviewPage: AggregateShipStatus + MoSection нос/корма + OverviewGroupCard (только ds/*)
- Client rollup `rollupTree` / `worstOf` — quarantine child → group/ship NOT good
- Hooks: `useAssetsTree` (GET tree, staleTime 60s) + `useOverviewRealtime` (WS values ≤100 tags → RQ cache)
- States: loading skeleton, error+retry, empty «Данные собираются с {first_sample_ts}», partial QuarantineBanner, stale desaturate
- DrillDownStubModal T-006 «Мнемосхема — фаза 2» (не 404)
- Route `(authenticated)/overview` → OverviewPage; StatusBar из shell

## Файлы

- `frontend/src/features/overview/OverviewPage.tsx`
- `frontend/src/features/overview/useAssetsTree.ts`
- `frontend/src/features/overview/useOverviewRealtime.ts`
- `frontend/src/features/overview/DrillDownStubModal.tsx`
- `frontend/src/features/overview/MoSection.tsx`
- `frontend/src/features/overview/treeUtils.ts`
- `frontend/src/features/overview/OverviewPage.test.tsx`
- `frontend/src/app/(authenticated)/overview/page.tsx`
- `frontend/e2e/specs/overview/drill-stub.spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/features/overview/OverviewPage.test.tsx`
- итог: 4 passed (rollup + quarantine + drill + empty)
- scenario: `npx playwright test e2e/specs/overview/drill-stub.spec.ts` → 1 passed
- Scenario E2E: `e2e/specs/overview/drill-stub.spec.ts` (AC-1-04 drill stub)
- PW-02/07 full glance/quarantine → s16

## Integration check

- [x] GET `/api/assets/tree` ↔ `fetchAssetsTree` / `useAssetsTree` + MSW
- [x] GET `/api/sources/status` ↔ empty `first_sample_ts` (earliest `last_poll_ts`)
- [x] WS `values` ↔ `useOverviewRealtime` / `useWsChannel` (tag flatten ≤100)
- [x] DS `AggregateShipStatus` / `OverviewGroupCard` / `Lamp` / banners / `StateShell`
- [x] `data-testid` ship-status, overview-group, drill-stub-modal, overview-page
- [ ] Full PW-02/07 → s16
