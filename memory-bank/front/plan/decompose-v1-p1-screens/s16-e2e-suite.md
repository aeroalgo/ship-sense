# Шаг s16: Playwright PW-01..PW-10
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §8 all PW; DoD Playwright green (parent run)


**visible_ui:** no
**Design skills:** — (Playwright suite only, no UI feature code)

## Цель
E2E suite по §8: fixtures + specs PW-01..PW-10; stable data-testid selectors.

## Контекст
- **Consumes:** s01–s15 UI complete; docker/API or MSW playwright route mocks
- **Produces:** `frontend/e2e/specs/*`

## Файлы
- `frontend/e2e/fixtures/*` (Создание)
- `frontend/e2e/specs/pw-01-login-tiles.spec.ts` (Создание)
- `frontend/e2e/specs/pw-02-overview-glance.spec.ts` (Создание)
- `frontend/e2e/specs/pw-03-journal-filter-print.spec.ts` (Создание)
- `frontend/e2e/specs/pw-04-trends-deeplink.spec.ts` (Создание)
- `frontend/e2e/specs/pw-05-watch-print.spec.ts` (Создание)
- `frontend/e2e/specs/pw-06-stale-banner.spec.ts` (Создание)
- `frontend/e2e/specs/pw-07-quarantine-not-normal.spec.ts` (Создание)
- `frontend/e2e/specs/pw-08-ws-reconnect.spec.ts` (Создание)
- `frontend/e2e/specs/pw-09-theme-no-flash.spec.ts` (Создание)
- `frontend/e2e/specs/pw-10-handoff-watch.spec.ts` (Создание)

## Интерфейсы (lean — без кода)
- selectors: только data-testid из §3.4 / §8.1
- n/a component props

## TDD (красная → зелёная)
1. **Тест:** писать specs по шагам §8.2–8.11
2. **Запуск:** parent Playwright — сначала FAIL/infra
3. **Реализация:** добить gaps UI если красный из-за продукта (не hide)
4. **Запуск:** all PW green

## Подробный процесс выполнения
1. HARD: запуск только parent (не subagent).
2. Fixtures: roster, tree with quarantine, events, series, WS mock.
3. Theme flash: screenshot/contrast assert PW-09.
4. Не заменять E2E «manual smoke» в Handoff.

## Чекпоинт верификации
- 10 specs существуют и проходят у parent
- Report path в implement Handoff
