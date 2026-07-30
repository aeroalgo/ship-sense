# Шаг s11: HealthSnapshot loop (psutil + pg sizes + queue callback)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S11 (из плана §224, §1121–1144: 60s snapshot, fields disk/ram/cpu/pg/queue/extra, structured logs)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `Health` (или HealthSnapshotService) — фоновый loop (60s) собирает psutil (disk, ram, cpu), pg sizes (samples/events), queue_depth (callback от T-001), persist в health_snapshots + structured logs. Graceful stop.

## Контекст
- **Consumes:** s04 health_snapshots, s05 schemas, psutil, writer queue depth hook.
- **Produces:** apps/edge/storage/health.py.
- **Downstream:** T-003 (latest/history), quota alert, observability.
- **План:** §1126 (extra examples), §1138 (logs), §226 (fields).

## Файлы
- `apps/edge/storage/health.py` (Создание)
- `tests/storage/test_health_snapshot.py` (Создание)

## Интерфейсы (lean — без кода)
- class HealthSnapshotService:
  - async def start(self) -> None: ...
  - async def stop(self) -> None: ...
  - async def snapshot_once(self, queue_depth: int = 0, extra: dict | None = None) -> HealthRow: ...
- HealthRow: captured_at, disk_*, ram_pct, cpu_pct, samples_bytes, events_bytes, extra
- Callback: writer передает queue_depth из T-001.

## TDD
- **Да:** unit mock psutil/pg → snapshot row; integration persist.
- pytest -k "health_snapshot"

## Подробный процесс выполнения
1. Periodic task (asyncio.create_task + sleep 60).
2. Сбор: psutil.disk_usage, virtual_memory, cpu_percent; SQL pg_total_relation_size('samples'), events.
3. Insert health_snapshots.
4. Structured log `storage.health.snapshot`.
5. extra: alert если есть, writer_last_flush_ms, chunks count и т.д.
6. Stop: cancel task.

## Верификация
- Каждые 60s новая строка.
- При disk 81% extra.alert="disk_80".
- queue_depth из callback.
- Блокер: s04, s09 (для queue hook).

## Блокеры / CREATIVE
Нет.
