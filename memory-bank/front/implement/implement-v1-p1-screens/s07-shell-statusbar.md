# [T-004 | s07 | shell-statusbar] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s07-shell-statusbar.md](../../plan/decompose-v1-p1-screens/s07-shell-statusbar.md)
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

- App shell `(authenticated)`: sticky StatusBar + AppNav + banner slots + QueryClient
- Routes §4.2: `/overview` `/journal` `/trends` `/watch` (placeholders StateShell loading)
- `useStatusBarAlarms`: REST bootstrap `GET /api/events?limit=20&severity=alarm` + WS `events`
- Alarm chip → `/journal?asset_id=&from=`; `ws-status` indicator; ThemeSwitcher in StatusBar
- SessionChip slot deferred → s08
- Fix: `WatchSection` `"use client"` (hooks without directive broke RSC barrel)

## Файлы

- `frontend/src/app/(authenticated)/layout.tsx`
- `frontend/src/app/(authenticated)/{overview,journal,trends,watch}/page.tsx`
- `frontend/src/features/shell/{AppNav,AppShell,QueryProvider,useStatusBarAlarms}.tsx|.ts`
- `frontend/src/features/shell/AppNav.test.tsx`
- `frontend/src/features/shell/StatusBar.alarms.test.tsx`
- `frontend/src/app/layout.tsx` — QueryProvider
- `frontend/src/components/ds/WatchSection.tsx` — use client
- `frontend/e2e/specs/shell/app-shell-nav.spec.ts`
- `frontend/package.json` — `@tanstack/react-query`

## Тесты

- cmd: `cd frontend && npm test -- src/features/shell/`
- итог: 4 passed (AppNav 3 + StatusBar click 1)
- scenario: `npx playwright test e2e/specs/shell/app-shell-nav.spec.ts` → 1 passed
- Scenario E2E: `e2e/specs/shell/app-shell-nav.spec.ts` (StatusBar sticky + nav → /journal)

## Integration check

- [x] StatusBar `data-testid=status-bar` ↔ plan AC-1-05 / PW shell
- [x] `ws-status` ↔ plan PW-08 testid
- [x] fetchEvents `/api/events` ↔ queryKeys.events + BOOTSTRAP limit/severity
- [x] useWsChannel `events` ↔ WsManager.subscribeEvents
- [x] env `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` ↔ `.env.example` (+ local `.env.local`)
- [ ] SessionChip logout — s08
- [ ] QuarantineBanner tags — s15
- [ ] PW-08 full reconnect — s16
