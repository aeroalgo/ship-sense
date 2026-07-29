# Шаг s04: OpenAPI types + REST client + MSW
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §15 OpenAPI types path; §5 API maps; DoD types.ts; T-003 mockable


**visible_ui:** no
**Design skills:** — (pure lib/api + MSW, no JSX)

## Цель
Typed REST client (`lib/api`) + types (codegen или hand-sync из BACK plan) + MSW fixtures для offline UI.

## Контекст
- **Consumes:** s01; BACK plan-v1-p1-api §6/§19 (или live openapi.json)
- **Produces:** fetch wrappers + Query keys; MSW handlers

## Файлы
- `frontend/src/lib/api/types.ts` (Создание)
- `frontend/src/lib/api/client.ts` (Создание) — base URL, credentials cookies
- `frontend/src/lib/api/assets.ts` (Создание) — GET /api/assets/tree
- `frontend/src/lib/api/events.ts` (Создание)
- `frontend/src/lib/api/series.ts` (Создание)
- `frontend/src/lib/api/setpoints.ts` (Создание)
- `frontend/src/lib/api/session.ts` (Создание) — roster/session
- `frontend/src/lib/api/reports.ts` (Создание) — watch report
- `frontend/src/lib/api/sources.ts` (Создание)
- `frontend/src/test/msw/handlers.ts` (Создание)
- `frontend/src/lib/api/client.test.ts` (Создание)

## Интерфейсы (lean — без кода)
- client: `apiGet|apiPost|apiDelete` — credentials include; parse error body
- modules: `fetchAssetsTree`, `fetchEvents`, `fetchSeries`, `fetchSetpoints`, `fetchRoster`, `createSession`, `deleteSession`, `fetchWatchReport`, `fetchSourcesStatus`
- types: имена `AssetsTreeResponse`, `EventsListResponse`, `SeriesResponse`, `WatchReportResponse`, `RosterResponse` (из BACK)
- header consumer: `X-Events-Reconstruction`

## TDD (красная → зелёная)
1. **Тест:** client.test — base URL join; 401 handling shape; MSW happy path assets.tree
2. Red → wrappers → green

## Подробный процесс выполнения
1. Синхронизировать types с OpenAPI (live) или mirror BACK plan examples.
2. React Query hooks — **не** в этом шаге (или тонкие `queryKeys` only); hooks в feature steps.
3. MSW: минимальные fixtures tree/events/series/roster/watch.

## Чекпоинт верификации
- Импорты types без any escape hatch на Quality
- §0.11: каждый client fn имеет MSW или e2e counterpart later
