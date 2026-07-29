# [T-004 | s11 | chart-wrapper] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s11-chart-wrapper.md](../../plan/decompose-v1-p1-screens/s11-chart-wrapper.md)
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

**Design read:** ship-bridge HMI trend strip (ISA-101) — VARIANCE 2 · MOTION 1–2 · DENSITY 9; signature = honest gaps + setpoint steps + severity markers; not Grafana chrome.

## Сделано

- `TrendChartContainer` — DS chrome (tag/unit/badge/quality) + `data-testid=trend-chart` + a11y summary
- `uplotAdapter` — thin uPlot leaf; `spanGaps: false`; null gaps via spike `seriesToUplotAligned`; draw setpoints + markers
- Props = `TrendChartProps` из `chart-lib-spec.ts`
- Storybook `DS/TrendChartContainer` (fixture + gaps demo)
- jsdom polyfills: `matchMedia` + canvas `getContext` + `Path2D` (для uPlot в Vitest)
- TrendsPage **не** подключали (s12)

## Файлы

- `frontend/src/components/ds/TrendChartContainer.tsx`
- `frontend/src/components/ds/TrendChartContainer.module.css`
- `frontend/src/components/ds/TrendChartContainer.test.tsx`
- `frontend/src/components/ds/TrendChartContainer.stories.tsx`
- `frontend/src/features/trends/chart/adapters/uplotAdapter.ts`
- `frontend/src/components/ds/index.ts` (export)
- `frontend/src/test/setup.ts` (canvas/Path2D/matchMedia)
- reference: `frontend/src/features/trends/spike/*`, `frontend/src/lib/trends/chart-lib-spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/components/ds/TrendChartContainer.test.tsx`
- итог: 3 passed (null gap AC-8-05; setpoint count AC-8-01; fixture §9.4 #5)
- Scenario E2E: n/a — DS chart wrapper; Trends page/marker deep-link → s12 / PW-03/04 → s16

## Integration check

- [x] data-testid `trend-chart` / `trend-chart-plot` / `trend-chart-setpoints` / `trend-chart-markers`
- [x] gaps AC-8-05 (null, not zero) via `assertNoZeroFilledGaps`
- [x] setpoints AC-8-01 partial (`data-setpoint-count` + legend chips)
- [x] `uplot` in package.json; `data-chart-lib=uplot`
- [x] spike kept as reference (imported by adapter)
- [x] TrendsPage not wired (s12)
- [ ] Full chart E2E / Live toggle → s12+s16
