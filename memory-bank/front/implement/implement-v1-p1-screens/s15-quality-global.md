# [T-004 | s15 | quality-global] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s15-quality-global.md](../../plan/decompose-v1-p1-screens/s15-quality-global.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

> **Skills:** не дублировать. Канон — decompose `s15-quality-global.md` (Design stack + Impl legacy).

## Сделано

- `useStaleGate` — threshold `NEXT_PUBLIC_STALE_THRESHOLD_SEC`; `body[data-stale]`; age + forceStale
- `FreshnessController` — WS/REST freshness + QuarantineBanner scope; chrome **вне** `#app-root` (z-index 40)
- AppShell: banners → `freshnessSlot`; `#app-root` только main (desaturate §2.2.3)
- `globals.css` — `body[data-stale="true"] #app-root { filter: saturate(0.55) brightness(0.92) }`
- Overview: убран локальный saturate/FreshnessBanner (глобальный gate); QuarantineBanner scope=обзор сохранён
- PW-06/07 → s16 (явно в step)

## Файлы

- `frontend/src/hooks/useStaleGate.ts`
- `frontend/src/hooks/useStaleGate.test.ts`
- `frontend/src/features/shell/FreshnessController.tsx`
- `frontend/src/features/shell/FreshnessController.test.tsx`
- `frontend/src/features/shell/AppShell.tsx`
- `frontend/src/app/(authenticated)/layout.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/styles/tokens/semantic-alarms.css` (dup CSS removed)
- `frontend/src/features/overview/OverviewPage.tsx`

## Тесты

- cmd: `cd frontend && npm test -- src/hooks/useStaleGate.test.ts src/features/shell/FreshnessController.test.tsx src/features/overview/OverviewPage.test.tsx`
- итог: 12 passed
- Scenario E2E: PW-06/07 deferred → s16 (`e2e/specs/shell/stale-banner.spec.ts`, `e2e/specs/overview/quarantine-rollup.spec.ts`)

## Integration check

- [x] `NEXT_PUBLIC_STALE_THRESHOLD_SEC` ↔ `.env.example` / `public-env.ts` / `useStaleGate`
- [x] `body[data-stale]` ↔ `globals.css` `#app-root` filter
- [x] FreshnessBanner вне `#app-root` (structure assert)
- [x] QuarantineBanner не green rollup (DS + scope tags)
- [ ] PW-06/07 → s16
