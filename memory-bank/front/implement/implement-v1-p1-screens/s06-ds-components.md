# [T-004 | s06 | ds-components] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s06-ds-components.md](../../plan/decompose-v1-p1-screens/s06-ds-components.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `playwright-best-practices`
- `next-best-practices`
- `frontend-design` *(visible UI — HARD)*
- `design-taste-frontend` *(visible UI — HARD)*
- `emil-design-eng` *(visible UI — HARD)*
- `impeccable` *(visible UI — HARD)*
- `high-end-visual-design` *(visible UI — HARD)*
- `ui-ux-pro-max` *(visible UI — HARD)*
- `verification-before-completion`

> Retro 2026-07-26: design stack зафиксирован как обязательный для visible UI (`workflow-implement` gate). В исходной сессии шага загружен частично/не загружен — следующие UI IMPLEMENT обязаны Read все 6 до кода.


## Сделано

- DS0-4 библиотека `components/ds/*` (кроме TrendChartContainer → s11)
- `Lamp`: SVG mask + tokens, `data-state` severity×quality, quarantine overlay ≠ good, pulse/reduced-motion
- `StateShell`: 5 variants loading/empty/error/partial/stale
- StatusBar, AggregateShipStatus, OverviewGroupCard, EventRow/Filters, TagPicker, Watch*, LoginTile, banners, PrintLayout, SessionChip + barrel `index.ts`
- Storybook 8 (react-vite): `npm run storybook` / `build-storybook` → `storybook-static` (G-DS0-4-04)
- Stories: Lamp matrix + StateShell 5 variants + StatusBar states + Catalog states per G-DS0-4-02
- Vitest cleanup в `test/setup.ts`

## Файлы

- `frontend/src/components/ds/Lamp.tsx` + `Lamp.module.css` + `Lamp.test.tsx` + `Lamp.stories.tsx`
- `frontend/src/components/ds/StateShell.tsx` + `StateShell.test.tsx` + `StateShell.stories.tsx`
- `frontend/src/components/ds/{StatusBar,AggregateShipStatus,OverviewGroupCard,EventRow,EventFilters,TagPicker,WatchVerdict,WatchSection,LoginTile,FreshnessBanner,QuarantineBanner,PrintLayout,SessionChip}.tsx`
- `frontend/src/components/ds/StatusBar.stories.tsx` + `Catalog.stories.tsx` + `index.ts`
- `frontend/.storybook/{main.ts,preview.tsx}`
- `frontend/package.json` (storybook scripts + deps)
- `frontend/src/test/setup.ts` (RTL cleanup)

## Тесты

- cmd: `cd frontend && npm test -- src/components/ds/`
- итог: 7 passed (Lamp 5 + StateShell 2)
- Storybook: `CI=1 npm run build-storybook` → exit 0, output `frontend/storybook-static`
- Scenario E2E: n/a — component library gate; screen flows → s07+

## Integration check

- [x] Lamp SVG paths ↔ `public/ds/lamps/*` + `lamp-grammar-spec.ts`
- [x] data-testid prefixes ↔ plan §3.4
- [x] tokens ↔ `SEVERITY_COLOR_TOKEN` / `QUALITY_COLOR_TOKEN` (no hardcoded hex)
- [x] Storybook staticDirs ↔ `public/`
- [ ] storage keys — n/a
- [ ] env — n/a
- [ ] scenario E2E — n/a (DS catalog; PW screens at s07+)
