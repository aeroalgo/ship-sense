# FRONT TASK — browser API mock + DesignSwitcher

**Дата:** 2026-07-26  
**ID:** task-20260726-api-mock-design-switcher  
**Команда:** FRONT TASK  
**Статус:** done

## Формулировка

1. В `npm run dev` экраны наполняются mock REST без живого backend (`NEXT_PUBLIC_API_MOCK=1`).
2. В AppShell + login виден `DesignSwitcher` (d01…d05).

## Skills

**Impl:** tdd · frontend-testing · playwright-best-practices · vercel-react-best-practices · vercel-composition-patterns · next-best-practices · verification-before-completion · requesting-code-review

**Design stack:** frontend-design · design-taste-frontend · emil-design-eng · impeccable · high-end-visual-design · ui-ux-pro-max

## Ход

- MSW browser worker + `ApiMockProvider` gate
- Handlers `*/api/*` shared node/browser
- Fixture: дерево НДО/КДО/ГЭУ/ВДГ + KKS из РД АПС/СКТ (`docs/`), roster 4 роли
- DesignSwitcher в StatusBar и Login
- Vitest green после sync тестов под richer fixtures

## Handoff

- **Done:** browser API mock (`NEXT_PUBLIC_API_MOCK=1`) + DesignSwitcher; fixtures ближе к РД (KKS, НДО/КДО, alarm.HH)
- **Files:** `ApiMockProvider.tsx`, `test/msw/browser.ts`, `handlers.ts`, `fixtures.ts`, `AppShell.tsx`, `LoginPage.tsx`, `AppearanceProviders.tsx`, `.env.local`/`.env.example`, `public/mockServiceWorker.js`
- **Next:** restart `npm run dev`; open `/login` → tiles; cycle design button. Then `FRONT IMPLEMENT` s16
- **Tool / model:** Cursor + Composer
- **New chat:** yes (task done → s16)
