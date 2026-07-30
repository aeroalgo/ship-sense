# Шаг s01: WriterService.start_tcp + run_tcp refactor
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-PIPE-06
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Добавить `WriterService.start_tcp` с возвратом bound `(host, port)` после `start_server` (в т.ч. `port=0`). Рефактор `run_tcp` → делегирует в `start_tcp` + `writer_loop` + `shutdown`. `__main__` поведение compose не ломается.

## Контекст
- **Consumes:** существующий `WriterService.run_tcp` / `_handle_client` / `writer_loop` / `shutdown` (`apps/edge/storage/writer.py`); ADR-PIPE-003.
- **Produces:** публичный API `start_tcp` для L0/L1 harness; unit-тест bound port.

## Файлы
- `apps/edge/storage/writer.py` (Модификация)
- `tests/storage/test_writer_start_tcp.py` (Создание)
- `apps/edge/storage/__main__.py` (Verify only — по-прежнему `await service.run_tcp(...)`)

## Интерфейсы (lean — без кода)
- `async def start_tcp(self, host: str = "0.0.0.0", port: int = 0) -> tuple[str, int]` — `asyncio.start_server(self._handle_client, host, port)` → сохранить в `self._server`; если sockets пусты → `RuntimeError` с явной фразой; вернуть `(bound_host, bound_port)` из `getsockname()`.
- `async def run_tcp(self, host: str = "0.0.0.0", port: int = 9009) -> None` — `await self.start_tcp(host, port)` → try `writer_loop` / finally `shutdown` (как сейчас).
- Запрещено: monkeypatch `start_server` в тестах как обход отсутствия API; запрещён silent fallback при пустых sockets.

## TDD (красная → зелёная)
1. **Тест:** `tests/storage/test_writer_start_tcp.py`
   - `test_start_tcp_binds_ephemeral_port` — mock/minimal session+repos (как соседние writer unit) → `start_tcp("127.0.0.1", 0)` → port > 0; `shutdown` закрывает server.
   - `test_run_tcp_delegates_to_start_tcp` — проверить, что `run_tcp` вызывает `start_tcp` (spy) или интеграционно: listen на ephemeral + cancel.
   - Запуск: FAIL — `start_tcp` отсутствует.
2. **Реализация:** метод + рефактор `run_tcp`.
3. **Запуск:** targeted `.venv/bin/pytest tests/storage/test_writer_start_tcp.py -q` PASS; регрессия writer batch не ломается.

## Подробный процесс выполнения
1. Red: тест на отсутствие `start_tcp` / AttributeError.
2. Green: реализовать `start_tcp` по plan §3.4; `run_tcp` тонкий wrapper.
3. Убедиться: `__main__.py` не менять (кроме если импорт сломан — не должен).
4. Anti-patterns: нет bare except; RuntimeError явный при no sockets.

## Чекпоинт верификации
- AC-PIPE-06: ephemeral bind работает; `run_tcp` API совместим.
- `.venv/bin/pytest tests/storage/test_writer_start_tcp.py -q` — green.

## Зависимости
- Upstream: T-002 s09 WriterService — hard, есть.
- Downstream: s02–s06 harness.

## Frontend
N/A.

## Следующий шаг
→ s02 (Timescale testcontainer fixture).
