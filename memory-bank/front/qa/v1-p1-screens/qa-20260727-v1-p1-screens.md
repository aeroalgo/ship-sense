# FRONT QA — T-004 v1-p1-screens (+ task api-mock)

**Дата:** 2026-07-27  
**Scope:** s01–s16 + task `api-mock` / DesignSwitcher  
**Вердикт:** PASS (после фиксов)

## Checks

| Check | Result |
|-------|--------|
| Lint | N/A (нет eslint script в `frontend/package.json`) |
| Types `tsc --noEmit` | PASS (после фиксов) |
| Vitest unit/component | **104 passed** / 25 files |
| Playwright full | **19 passed** (PW-01..10 + scenario specs) |
| UX/a11y spot | PASS (minor notes) |
| Exploratory live | PASS (mock `:3000`) |
| Perf | soft: Google Fonts DNS fail offline → retry spam |
| Security | soft: public env only; WS без mock бьёт в `:8000` |

## Root causes (fixed)

1. **E2E × MSW collision:** `NEXT_PUBLIC_API_MOCK=1` на reused `:3000` → MSW глушил Playwright `page.route` → 10 fail (tiles 4≠3, groups 7≠4, quarantine 0, journal counts…).
   - Fix: `playwright.config.ts` — port **3100**, `NEXT_PUBLIC_API_MOCK=0`, readiness `/login`.
2. **drill-stub copy:** test `Мнемосхема — фаза 2` vs product `Мнемосхема: фаза 2`.
3. **tsc:** `FreshnessController` `.ts` → `source_ts`; `useWatchReport` dead `.error` (ApiResult throws); Lamp CSS var cast; MSW `severity: "critical"` → `"alarm"`.
4. **JournalPage.test** ожидания alarm-filter под fixture с `protection.trip`.

## Scenario paths (P0/P1)

- `frontend/e2e/specs/pw-01-login-tiles.spec.ts` … `pw-10-handoff-watch.spec.ts`
- `frontend/e2e/specs/session/login-tiles.spec.ts`
- `frontend/e2e/specs/overview/drill-stub.spec.ts`
- `frontend/e2e/specs/journal/no-ack-deeplink.spec.ts`
- `frontend/e2e/specs/trends/deep-link.spec.ts`
- `frontend/e2e/specs/watch/watch-compression.spec.ts` · `handoff-flow.spec.ts`
- `frontend/e2e/specs/shell/app-shell-nav.spec.ts` · `theme-switcher.spec.ts`

## Exploratory (live `:3000`, `NEXT_PUBLIC_API_MOCK=1`)

- OK login tiles + DesignSwitcher cycle → overview
- OK overview ≥4 groups + StatusBar design switcher
- OK journal без ack
- OK trends deeplink + watch
- Console: `ws://localhost:8000/api/stream` ERR_CONNECTION_REFUSED (MSW не мокает WS) — expected without backend; PW-06/08 покрывают WS через fixture mock

## UX / a11y findings

- DesignSwitcher / ThemeSwitcher: `aria-label` есть; touch min 48px
- Lamp: `role="img"` + aria-label; pulse respects reduced-motion (spec)
- Soft: WS reconnect noise в console при mock-only dev
- Soft: offline fonts.googleapis.com → Next font retry (не блокер тестов)

## Fixes applied (this QA)

- `frontend/playwright.config.ts`
- `frontend/src/features/shell/FreshnessController.tsx`
- `frontend/src/features/watch/useWatchReport.ts`
- `frontend/src/components/ds/Lamp.tsx`
- `frontend/src/test/msw/fixtures.ts`
- `frontend/src/features/journal/JournalPage.test.tsx`
- `frontend/e2e/specs/overview/drill-stub.spec.ts`
- `frontend/e2e/specs/trends/deep-link.spec.ts`

## Open / follow-up (не FAIL)

- Mock WS в browser MSW или suppress reconnect spam в mock mode
- Self-host fonts / offline-friendly font loading
- Optional: eslint pipeline

## Handoff

- **Done:** FRONT QA T-004 PASS — tsc + Vitest 104 + Playwright 19; e2e/MSW isolation fixed; type bugs fixed
- **Files:** `memory-bank/front/qa/v1-p1-screens/qa-20260727-v1-p1-screens.md` + fixes выше
- **Next:** `FRONT REFLECT` T-004 (s01–s16 + task); soft CR-UI-05; parallel BACK
- **Tool / model:** Cursor + Composer
- **New chat:** yes (QA done → REFLECT)
