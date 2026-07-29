# [T-004 | s16 | e2e-suite] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s16-e2e-suite.md](../../plan/decompose-v1-p1-screens/s16-e2e-suite.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

> **Skills:** A∪B — tdd, frontend-testing, playwright-best-practices, playwright-generate-test, next-best-practices, vercel-*, frontend-patterns, verification-before-completion, requesting-code-review. Design stack skip (`visible_ui: no`).

## Сделано

- Fixtures: roster/tree/events/series/setpoints/watch + `api.ts` / `ws-mock.ts`
- Specs PW-01..PW-10 (`e2e/specs/pw-0N-*.spec.ts`) по plan §8
- Gap UI: `data-testid=setpoint-line` / `event-marker` в TrendChartContainer
- Parent Playwright: **10 passed**

## Файлы

- `frontend/e2e/fixtures/*`
- `frontend/e2e/specs/pw-01-login-tiles.spec.ts` … `pw-10-handoff-watch.spec.ts`
- `frontend/src/components/ds/TrendChartContainer.tsx`

## Тесты

- cmd: `cd frontend && npx playwright test e2e/specs/pw-01-login-tiles.spec.ts e2e/specs/pw-02-overview-glance.spec.ts e2e/specs/pw-03-journal-filter-print.spec.ts e2e/specs/pw-04-trends-deeplink.spec.ts e2e/specs/pw-05-watch-print.spec.ts e2e/specs/pw-06-stale-banner.spec.ts e2e/specs/pw-07-quarantine-not-normal.spec.ts e2e/specs/pw-08-ws-reconnect.spec.ts e2e/specs/pw-09-theme-no-flash.spec.ts e2e/specs/pw-10-handoff-watch.spec.ts --reporter=list`
- итог: **10 passed** (6.8s)
- Scenario E2E: `frontend/e2e/specs/pw-01-*.spec.ts` … `pw-10-*.spec.ts` (полный suite §8)

## Integration check

- [x] selectors `data-testid` §8.1 ↔ specs
- [x] API mocks `localhost:8000` ↔ `NEXT_PUBLIC_API_URL`
- [x] WS mock `/api/stream` ↔ `NEXT_PUBLIC_WS_URL` (PW-06/08)
- [x] `setpoint-line` / `event-marker` ↔ TrendChartContainer
- [x] PW-06/07 закрыты (s15 deferred)
