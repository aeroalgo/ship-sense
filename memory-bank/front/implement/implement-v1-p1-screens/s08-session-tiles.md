# [T-004 | s08 | session-tiles] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s08-session-tiles.md](../../plan/decompose-v1-p1-screens/s08-session-tiles.md)
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

- `/login` + `LoginPage`: roster tiles sorted `tile_order`, tap → POST `/api/session` → redirect `default_screen` (1→`/overview`, 6→`/watch`)
- `SessionProvider` / `useSession`: person in sessionStorage, login/logout, 401 → clear + toast «Сессия завершена по таймауту» + `/login`
- `SessionChip` в StatusBar (AppShell); anonymous — chip hidden
- API client: `onUnauthorized` / `notifyUnauthorized` on 401 (`credentials: include` уже был)
- MSW POST session возвращает name/rank/default_screen из roster
- Scenario E2E PW-01: `e2e/specs/session/login-tiles.spec.ts`

## Файлы

- `frontend/src/app/login/page.tsx`
- `frontend/src/features/session/LoginPage.tsx`
- `frontend/src/features/session/useSession.tsx`
- `frontend/src/features/session/session.test.tsx`
- `frontend/src/features/session/AppearanceProviders.tsx` — SessionProvider
- `frontend/src/features/shell/AppShell.tsx` — SessionChip
- `frontend/src/lib/api/client.ts` — 401 notify
- `frontend/src/test/msw/handlers.ts` — session person lookup
- `frontend/e2e/specs/session/login-tiles.spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/features/session/session.test.tsx`
- итог: 6 passed
- regression: `npm test -- src/features/session/ src/features/shell/AppNav.test.tsx` → 25 passed; `client.test.ts` 5 passed
- scenario: `npx playwright test e2e/specs/session/login-tiles.spec.ts` → 1 passed
- Scenario E2E: `e2e/specs/session/login-tiles.spec.ts` (PW-01 ≤2 taps)

## Integration check

- [x] POST/DELETE `/api/session` ↔ `createSession`/`deleteSession` + MSW
- [x] GET `/api/watch/roster` ↔ `fetchRoster` + LoginPage
- [x] `credentials: include` ↔ cookie session calls
- [x] `data-testid=login-tile` / `session-chip` ↔ plan PW-01
- [x] 401 → toast copy plan §6.1
- [x] anonymous `/overview` без chip §6.2
- [ ] Full PW-01..10 suite → s16
