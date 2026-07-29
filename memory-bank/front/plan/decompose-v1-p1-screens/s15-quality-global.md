# Шаг s15: Global stale desaturate + quarantine banners
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §2.2.3; PW-06/07; quality never masked as norm


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Глобальный `data-stale` overlay + FreshnessBanner поверх; QuarantineBanner scope; единый stale detection из WS/REST.

## Контекст
- **Consumes:** s05 WS stale events, s06 banners, s07 shell
- **Produces:** features/shell freshness controller

## Файлы
- `frontend/src/features/shell/FreshnessController.tsx` (Создание)
- `frontend/src/hooks/useStaleGate.ts` (Создание)
- `frontend/src/app/(authenticated)/layout.tsx` (Модификация) — wire controller
- `frontend/src/app/globals.css` (Модификация) — body[data-stale] filter §2.2.3
- `frontend/src/features/shell/FreshnessController.test.tsx` (Создание)

## Интерфейсы (lean — без кода)
- hook: `useStaleGate` — threshold NEXT_PUBLIC_STALE_THRESHOLD_SEC; sets data-stale on body
- FreshnessBanner z-index **выше** desaturate overlay
- QuarantineBanner lists tags/scope; never green rollup

## TDD (красная → зелёная)
1. **Тест:** stale true → attribute set; banner visible
2. **Тест:** banner not affected by parent filter (structure assertion)
3. Parent Vitest; PW-06/07 in s16

## Подробный процесс выполнения
1. CSS exactly §2.2.3 saturate/brightness.
2. Integrate with overview good→stale transitions.
3. Нет маскировки quarantine под норму.

## Чекпоинт верификации
- PW-06/07 scenarios implementable
- Desaturate не на баннере
