# [T-004 | s05 | ws-manager] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s05-ws-manager.md](../../plan/decompose-v1-p1-screens/s05-ws-manager.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `verification-before-completion`

## Сделано

- `WsManager`: connect / subscribeValues / subscribeEvents / unsubscribe / singleton `getWsManager`
- Protocol types mirror BACK §7 (`subscribe`, `value`, `event`, `CURSOR_EXPIRED`, hello/ack)
- Tag budget: `WS_MAX_TAGS=100` — strict → `TagBudgetError`; default → split chunks
- Reconnect: exponential backoff (250ms…5s), resubscribe last set + `resume_cursor`
- Out events: `value` | `event` | `stale` | `disconnect` | `cursor_expired` | `connected` | `reconnecting`
- Hook `useWsChannel`: mount subscribe / unmount unsubscribe

## Файлы

- `frontend/src/lib/ws/types.ts`
- `frontend/src/lib/ws/manager.ts`
- `frontend/src/lib/ws/manager.test.ts`
- `frontend/src/hooks/useWsChannel.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/lib/ws/manager.test.ts`
- итог: 9 passed (payload shape ×2, tag strict/split, reconnect resume, cursor_expired, stale, singleton, unmount cleanup)
- Scenario E2E: n/a — нет user-visible UI (PW-08 → s07 shell)

## Integration check

- [x] WS frames ↔ BACK plan §7 (`action/subscribe`, `CURSOR_EXPIRED`, resume_cursor)
- [x] `NEXT_PUBLIC_WS_URL` ↔ `.env.example` / `getWsUrl`
- [x] Tag max 100 ↔ FRONT §5.1.6 / BACK `API_WS_MAX_TAGS`
- [x] Hook cleanup ↔ unmount unsubscribe
- [ ] storage keys — n/a
- [ ] DB cols — n/a
- [ ] scenario E2E — n/a (lib-only; PW-08 at s07)
