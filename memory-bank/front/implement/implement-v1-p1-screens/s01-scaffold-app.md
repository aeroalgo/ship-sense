# [T-004 | s01 | scaffold-app] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s01-scaffold-app.md](../../plan/decompose-v1-p1-screens/s01-scaffold-app.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `next-best-practices`
- `verification-before-completion`

## Сделано

- Scaffold `frontend/`: Next.js 15 App Router + React 19 + TS strict
- Scripts: `dev`, `build`, `start`, `test`, `test:watch`, `test:e2e`
- Vitest+RTL setup + smoke (env §4.4 keys)
- Playwright config (`baseURL` localhost:3000, `e2e/specs`)
- `.env.example` — 3 публичных переменных
- Root layout импортирует `globals.css` → `styles/tokens/index.css` (CR-UI-01)
- `html` defaults: `data-design="d01"` `data-theme="day"`
- `/` → `redirect("/login")` (stub, без экранов/DS)
- Дерево каталогов §4.1 уже было от CREATIVE; дописаны configs + app shell

## Файлы

- `frontend/package.json`
- `frontend/next.config.ts`
- `frontend/tsconfig.json`
- `frontend/vitest.config.ts`
- `frontend/playwright.config.ts`
- `frontend/.env.example`
- `frontend/.gitignore`
- `frontend/next-env.d.ts`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/lib/env/public-env.ts`
- `frontend/src/test/setup.ts`
- `frontend/src/test/smoke.test.ts`

## Тесты

- cmd: `cd frontend && npm test`
- итог: 3 passed (smoke)
- cmd: `cd frontend && npm run build`
- итог: OK (Next.js 15.5.22)

## Integration check

- [x] env vars in `.env.example` ↔ `PUBLIC_ENV_KEYS` / plan §4.4
- [x] tokens CSS import path layout → globals → tokens/index (CR-UI-01)
- [ ] storage keys — n/a (s02)
- [ ] DB cols — n/a
- [ ] events ↔ handlers — n/a
- [ ] scenario E2E — n/a (scaffold; user flows → s08+/s16)
