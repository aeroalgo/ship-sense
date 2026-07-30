# Шаг s02: Theme/Design providers + switchers
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** yes (CR-UI-01) — **closed**; soft CR-UI-05 — **closed** | **tdd:** yes
**AC:** G-DS0-4-03 (theme no flash — partial); CR-UI-01 AC; CR-UI-05 floor tokens; 5×3 attr switch

**Creative:** [CR-UI-01-tokens.md](../../creative/v1-p1-screens/CR-UI-01-tokens.md); [CR-UI-05-post-density.md](../../creative/v1-p1-screens/CR-UI-05-post-density.md) + `frontend/src/lib/theme/post-density-spec.ts`


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Подключить уже созданные token CSS (CR-UI-01): ThemeProvider + DesignProvider, blocking script anti-flash, ThemeSwitcher (продукт) + DesignSwitcher (preview), persist localStorage. Type/touch floor — CR-UI-05.

## Контекст
- **Consumes:** s01; [CR-UI-01-tokens.md](../../creative/v1-p1-screens/CR-UI-01-tokens.md); [CR-UI-05-post-density.md](../../creative/v1-p1-screens/CR-UI-05-post-density.md); plan §2.2–2.5
- **Produces:** providers, hooks, switchers; layout import tokens
- **Already on disk:** `styles/tokens/**` (5 skins × day/night/dim + semantic + density floor), `lib/theme/types.ts`, `switcher-spec.ts`, `post-density-spec.ts`

## Файлы
- `frontend/src/styles/tokens/*` (Уже есть — не пересоздавать; править только при утверждении skin)
- `frontend/src/features/session/ThemeProvider.tsx` (Создание) — или AppearanceProvider
- `frontend/src/hooks/useTheme.ts` (Создание)
- `frontend/src/hooks/useDesign.ts` (Создание)
- `frontend/src/components/ds/ThemeSwitcher.tsx` (Создание)
- `frontend/src/components/ds/DesignSwitcher.tsx` (Создание) — gate preview
- `frontend/src/app/layout.tsx` (Модификация) — import tokens + blocking script + `data-theme`/`data-design`
- `frontend/src/features/session/theme.test.ts` (Создание)
- `frontend/src/features/session/design.test.ts` (Создание)

## Интерфейсы (lean — без кода)
- tokens: см. CR-UI-01 §6 + `ThemeTokens` в `lib/theme/types.ts`
- `ThemeSwitcher` — props: `theme`, `onChange`; testid `theme-switcher`
- `DesignSwitcher` — props: `design`, `onChange`; testid `design-switcher`; только preview
- hooks: cycle theme/design; persist `shipsense-theme` / `shipsense-design`
- attrs: `data-theme` + `data-design` на `<html>`

## TDD (красная → зелёная)
1. **Тест:** theme/design cycle, localStorage round-trip, defaults day/d01, reject invalid
2. **Запуск:** FAIL
3. **Реализация:** providers + switchers + layout script
4. **Запуск:** PASS; visual: no white flash (PW later)

## Подробный процесс выполнения
1. CR-UI-01 уже закрыт — читать creative §7–8, §11.
2. Import `tokens/index.css` в layout; blocking script до paint.
3. ThemeProvider + DesignProvider (или один AppearanceProvider).
4. DesignSwitcher только при `isDesignPreviewEnabled()`.
5. CR-UI-05/Q9 — **closed** (waiver + floor); photo evidence после полевых замеров (§8 creative).

## Чекпоинт верификации
- day/night/dim без `#ffffff` flash
- d01…d05 переключаются в preview
- Alarm computed style не меняется при смене design
- Токены через var() в будущих компонентах
