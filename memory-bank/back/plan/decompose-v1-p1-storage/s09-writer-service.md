# Шаг s09: WriterService (IPC server + batch flush loop + NOTIFY)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S09 (из плана §223–228, §815–879: flush p95<100ms @586/s, batch, clock pre-check, NOTIFY, graceful drain)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `WriterService` — отдельный процесс: слушает length-prefixed IPC (как stub 9009), буферит TelemetrySample/Event, flush по таймеру/размеру, делегирует TimeAxis (clock), SamplesRepo, EventsRepo; после commit — NOTIFY shipsense_live; graceful shutdown drain 30s.

## Контекст
- **Consumes:** s06 SamplesRepo, s07 EventsRepo, s08 TimeAxis, T-001 IpcCanonicalSink framing + TelemetrySample/Event (из collector.domain.models — import path будет shared или copy до T-002 пакета).
- **Produces:** apps/edge/storage/writer.py; entrypoint для compose (заменит writer-stub).
- **Downstream:** T-003 (NOTIFY hint), s10 quota, s11 health.
- **План:** §834 (loop), §862 (flush), §871 (backpressure), §1174 (NOTIFY), §228 (drain).

## Файлы
- `apps/edge/storage/writer.py` (Создание — WriterService, writer_loop, flush_batches)
- `apps/edge/storage/__main__.py` или writer entry (если нужно)
- `tests/storage/test_writer_batch.py` (Создание)
- `docker-compose.yml` (позже s17 — замена writer-stub)

## Интерфейсы (lean — без кода)
- class WriterService:
  - async def run(self) -> None: ...  # listen IPC, loop
  - async def shutdown(self, timeout: float = 30.0) -> None: ...
- async def writer_loop(queue, repos, cfg)
- flush_batches: partition clock, SamplesRepo.insert, EventsRepo.insert, commit, NOTIFY
- Config: flush_interval_ms, max_batch_*, copy_threshold, retry backoff.

## TDD
- **Да:** unit на loop (timeout flush), flush partition clock, dedup count, NOTIFY emit.
- Integration: fake IPC client → writer → DB count.
- Targeted pytest -k "writer"

## Подробный процесс выполнения
1. IPC listener: asyncio.start_server, length-prefix decode → pydantic TelemetrySample | Event (reuse или adapter из T-001 models).
2. Батч: list + timeout 100ms / size 5000.
3. Перед flush: TimeAxis.detect + record clock events.
4. insert + commit.
5. await conn.execute("NOTIFY shipsense_live, 'batch'");
6. Metrics + logs.
7. Backpressure: если queue >90% — upstream (T-001) должен stall, не drop.
8. Graceful: drain pending, flush, close.

## Верификация
- 586/s 120s → zero drops, p95 flush <100ms.
- Clock shift в batch → event + log.
- NOTIFY виден в psql LISTEN.
- SIGTERM → drain exit 0.
- Блокер: s06–s08, T-001 canonical contract (s17).

## Блокеры / CREATIVE
Нет. IPC framing уже в stub/collector.
