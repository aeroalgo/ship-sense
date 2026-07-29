# [T-004 | s04 | api-client] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s04-api-client.md](../../plan/decompose-v1-p1-screens/s04-api-client.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `verification-before-completion`
- `next-best-practices` (lean — env/base URL)

## Сделано

- Typed REST client: `apiGet` / `apiPost` / `apiDelete` — `credentials: include`, error envelope → `ApiError`
- OpenAPI-mirror types: `AssetsTreeResponse`, `EventsListResponse`, `SeriesResponse`, `WatchReportResponse`, `RosterResponse`, …
- Modules: assets, events (+ `X-Events-Reconstruction`), series, setpoints, session, reports, sources
- Thin `queryKeys` only (RQ hooks — later feature steps)
- MSW handlers + fixtures for offline UI; dep `msw@^2`

## Файлы

- `frontend/src/lib/api/types.ts`
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/api/query-keys.ts`
- `frontend/src/lib/api/assets.ts`
- `frontend/src/lib/api/events.ts`
- `frontend/src/lib/api/series.ts`
- `frontend/src/lib/api/setpoints.ts`
- `frontend/src/lib/api/session.ts`
- `frontend/src/lib/api/reports.ts`
- `frontend/src/lib/api/sources.ts`
- `frontend/src/lib/api/client.test.ts`
- `frontend/src/test/msw/handlers.ts`
- `frontend/src/test/msw/fixtures.ts`
- `frontend/src/test/msw/server.ts`
- `frontend/package.json` (+ msw)

## Тесты

- cmd: `cd frontend && npm test -- src/lib/api/client.test.ts`
- итог: 5 passed (join URL ×2, 401 shape, assets.tree MSW, events reconstruction header)
- Scenario E2E: n/a — нет user-visible UI (lib + MSW)

## Integration check

- [x] Types ↔ BACK plan §6 examples / FRONT §15 (`Quality` from `lib/quality`)
- [x] `NEXT_PUBLIC_API_URL` ↔ `.env.example` / `getApiBaseUrl`
- [x] Client fns ↔ MSW handlers (tree/events/series/setpoints/reports/roster/session/sources)
- [x] `X-Events-Reconstruction` ↔ `fetchEvents().reconstruction`
- [ ] storage keys — n/a
- [ ] DB cols — n/a
- [ ] scenario E2E — n/a (lib-only)
