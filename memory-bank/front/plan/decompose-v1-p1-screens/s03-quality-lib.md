# Шаг s03: Quality rollup + event priority sort
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §5.1.4 worst-of; §5.2.4 sort; §9.4 TDD order #1; §16 rollup


**visible_ui:** no
**Design skills:** — (pure lib, no JSX)

## Цель
Чистые функции `lib/quality` (worst-of rollup) и `lib/events/priority` (журнал sort) — до UI.

## Контекст
- **Consumes:** s01; Quality enum plan §15
- **Produces:** shared helpers для Overview/Journal/StatusBar

## Файлы
- `frontend/src/lib/quality/rollup.ts` (Создание)
- `frontend/src/lib/quality/types.ts` (Создание) — Quality, AggregateStatus имена
- `frontend/src/lib/events/priority.ts` (Создание)
- `frontend/src/lib/quality/rollup.test.ts` (Создание)
- `frontend/src/lib/events/priority.test.ts` (Создание)

## Интерфейсы (lean — без кода)
- type: `Quality` — good|bad|uncertain|stale|quarantine
- type: `AggregateStatus` — Quality | unknown
- fn: `worstOf(qualities)` — порядок quarantine > stale > bad > uncertain > good
- fn: `rollupNode(childrenStatuses)` — group NOT green if any quarantine
- fn: `sortEvents(events)` — active-unacked → damage class → ts desc

## TDD (красная → зелёная)
1. **Тест:** rollup.test — матрица worst-of; quarantine beats good; empty→unknown
2. **Тест:** priority.test — active block first; damage class order; stable tie-break
3. Red → implement → green (parent Vitest)

## Подробный процесс выполнения
1. Зафиксировать enum names = BACK OpenAPI / plan §15.
2. Таблица damage class в priority.ts (разнос → масло → t°) — имена констант.
3. Без React — чистые функции.

## Чекпоинт верификации
- Vitest green
- quarantine anywhere → not good
- Нет UI imports
