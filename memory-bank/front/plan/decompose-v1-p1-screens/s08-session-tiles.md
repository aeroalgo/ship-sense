# Шаг s08: Session tiles B11 login/logout
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §6.1–6.2; PW-01 ≤2 taps; cookie session


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
`/login` плитки roster → POST session → redirect default_screen; logout DELETE; anonymous overview allowed.

## Контекст
- **Consumes:** s04 session API, s06 LoginTile/SessionChip, s07 layout
- **Produces:** features/session + login page

## Файлы
- `frontend/src/app/login/page.tsx` (Создание)
- `frontend/src/features/session/LoginPage.tsx` (Создание)
- `frontend/src/features/session/useSession.tsx` (Создание)
- `frontend/src/features/session/session.test.tsx` (Создание)
- `frontend/src/app/(authenticated)/layout.tsx` (Модификация) — SessionChip

## Интерфейсы (lean — без кода)
- hook: `useSession` — person, login(personId), logout, on401→clear
- page: LoginTile grid sorted `tile_order`; tap → POST /api/session
- redirect: default_screen 1→/overview, 6→/watch
- anonymous: /overview без cookie; SessionChip hidden

## TDD (красная → зелёная)
1. **Тест:** login success redirect; logout clears chip; 401 toast path
2. RTL + MSW
3. Parent Vitest green (E2E PW-01 в s16)

## Подробный процесс выполнения
1. GET /api/watch/roster → tiles.
2. ≤2 касания до целевого экрана (§6.1).
3. Copy без «AI»; timeout message «Сессия завершена по таймауту».

## Чекпоинт верификации
- Cookie credentials include на session calls
- Безличный режим §6.2
