# Шаг s01: Scaffold Next.js 15 + Vitest + Playwright + env
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** DoD scaffold (package runnable); plan §4.1 tree roots; §4.4 env vars present


**visible_ui:** no
**Design skills:** — (scaffold/tooling; UI screens later)

## Цель
Поднять каркас `frontend/` (Next.js 15 App Router, React 19, TS strict, Vitest, Playwright, env) без экранов и DS-компонентов.

## Контекст
- **Consumes:** plan §1.3 Tech, §4.1 tree, §4.4 env; techContext frontend
- **Produces:** runnable Next app + test runners; пустые route stubs optional

## Файлы
- `frontend/package.json` (Создание)
- `frontend/next.config.ts` (Создание)
- `frontend/tsconfig.json` (Создание)
- `frontend/vitest.config.ts` (Создание)
- `frontend/playwright.config.ts` (Создание)
- `frontend/.env.example` (Создание) — NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL, NEXT_PUBLIC_STALE_THRESHOLD_SEC
- `frontend/src/app/layout.tsx` (Создание) — root shell placeholder
- `frontend/src/app/page.tsx` (Создание) — redirect stub `/login`
- `frontend/src/app/globals.css` (Создание)
- `frontend/src/test/setup.ts` (Создание)
- `frontend/src/test/smoke.test.ts` (Создание)

## Интерфейсы (lean — без кода)
- env: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_STALE_THRESHOLD_SEC`
- scripts: `dev`, `build`, `test`, `test:e2e` в package.json
- n/a для UI contracts

## TDD (красная → зелёная)
1. **Тест:** `frontend/src/test/smoke.test.ts` — assert true / env example keys parsed helper
2. **Запуск:** parent `npm test` — FAIL до scaffold
3. **Реализация:** init Next + configs
4. **Запуск:** smoke PASS; `npm run build` OK

## Подробный процесс выполнения
1. Создать `frontend/` по plan §4.1 (корни app/components/features/lib/hooks/styles/e2e).
2. Зафиксировать Next 15 + React 19 + TS strict; CSS Modules default (без Tailwind до CR-UI-01).
3. Подключить Vitest+RTL setup; Playwright config (baseURL localhost).
4. `.env.example` с тремя публичными переменными §4.4.
5. Не реализовывать DS/экраны — только каркас.

## Чекпоинт верификации
- `frontend/package.json` существует, scripts полные
- Vitest smoke green (parent)
- Нет hardcoded API host вне env
