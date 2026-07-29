# Шаг s05: WS manager subscribe/resume/reconnect
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** plan §4.3 StatusBar WS; §5.1.6; AC-1-06 reconnect ≤5s; PW-08


**visible_ui:** no
**Design skills:** — (pure lib/ws, no JSX)

## Цель
Единый WebSocket manager: channels values/events, tag budget, resume после reconnect, CURSOR_EXPIRED→refetch signal.

## Контекст
- **Consumes:** s01, s04 (URL); BACK WS contract
- **Produces:** `lib/ws` + hooks stub for features

## Файлы
- `frontend/src/lib/ws/manager.ts` (Создание)
- `frontend/src/lib/ws/types.ts` (Создание)
- `frontend/src/lib/ws/manager.test.ts` (Создание)
- `frontend/src/hooks/useWsChannel.ts` (Создание)

## Интерфейсы (lean — без кода)
- class/api: `WsManager` — connect, subscribeValues(tagIds), subscribeEvents, unsubscribe, onReconnect
- events out: `value`, `event`, `stale`, `disconnect`, `cursor_expired`
- rule: max 100 tags per subscribe (plan §5.1.6)
- hook: `useWsChannel` — mount subscribe / unmount cleanup

## TDD (красная → зелёная)
1. **Тест:** mock WebSocket — subscribe payload shape; reconnect resubscribe; tag cap error/split
2. Red → implement → green

## Подробный процесс выполнения
1. Native WebSocket + exponential backoff reconnect.
2. Shared singleton across Overview/Trends/StatusBar.
3. Не парсить бизнес-rollup здесь — только transport.

## Чекпоинт верификации
- Unmount снимает подписку
- Reconnect восстанавливает last subscription set
- Unit tests без реального сервера
