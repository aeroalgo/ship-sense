# [T-004 | s02 | tokens-themes] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s02-tokens-themes.md](../../plan/decompose-v1-p1-screens/s02-tokens-themes.md)
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

- ThemeProvider + DesignProvider + AppearanceProviders (layout wrap)
- hooks `useTheme` / `useDesign` (re-export)
- ThemeSwitcher (продукт) + DesignSwitcher (preview gate)
- storage helpers + anti-flash blocking script (`beforeInteractive`)
- Preview page `/dev/appearance` для switchers + alarm sample
- Fix `isDesignPreviewEnabled` — прямой `process.env.NODE_ENV` (клиентский bundle)
- `.env.example`: `NEXT_PUBLIC_DESIGN_PREVIEW`
- Playwright scenario: theme ×2 → dim; design cycle; alarm color stable

## Файлы

- `frontend/src/lib/theme/storage.ts`
- `frontend/src/lib/theme/anti-flash-script.ts`
- `frontend/src/lib/theme/switcher-spec.ts` (gate fix)
- `frontend/src/features/session/ThemeProvider.tsx`
- `frontend/src/features/session/DesignProvider.tsx`
- `frontend/src/features/session/AppearanceProviders.tsx`
- `frontend/src/features/session/theme.test.tsx`
- `frontend/src/features/session/design.test.tsx`
- `frontend/src/hooks/useTheme.ts`
- `frontend/src/hooks/useDesign.ts`
- `frontend/src/components/ds/ThemeSwitcher.tsx`
- `frontend/src/components/ds/DesignSwitcher.tsx`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/dev/appearance/page.tsx`
- `frontend/src/app/dev/appearance/AppearanceControls.tsx`
- `frontend/e2e/specs/theme-switcher.spec.ts`
- `frontend/playwright.config.ts`
- `frontend/.env.example`

## Тесты

- cmd: `cd frontend && npm test -- src/features/session/ src/test/smoke.test.ts`
- итог: 19 passed
- cmd: `cd frontend && npx playwright test e2e/specs/theme-switcher.spec.ts`
- итог: 1 passed (scenario theme→dim + design + alarm stable)
- cmd: `cd frontend && npm run build`
- итог: OK

## Integration check

- [x] storage keys `shipsense-theme` / `shipsense-design` ↔ providers + anti-flash script
- [x] env `NEXT_PUBLIC_DESIGN_PREVIEW` ↔ `.env.example` + `isDesignPreviewEnabled`
- [x] tokens CSS import layout → globals → tokens/index (s01)
- [ ] DB cols — n/a
- [ ] events ↔ handlers — n/a
- [x] scenario E2E — `frontend/e2e/specs/theme-switcher.spec.ts`
