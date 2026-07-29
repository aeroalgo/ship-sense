# Шаг s08: TimeAxisService (official_ts, clock_shift detect)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S08 (из плана §206–213, §619–672: compute_official_ts, clock shift >60s, bad year, journal order)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `TimeAxisService` — pure + persist: compute_official_ts по rule (prefer source или edge), detect clock shift (backward 60s / forward 300s), append clock_shift event + log row. Config из timezone.yaml.

## Контекст
- **Consumes:** s07 events_repo (для clock event), s04 clock_shift_log, ship-pack timezone.
- **Produces:** apps/edge/storage/time_axis.py; shared helper для T-001 (duplicate до merge).
- **Upstream:** T-001 B7 stamps (source/edge_ts).
- **Downstream:** s09 writer (pre-check), T-003 (display official).
- **План:** §630 (algo), §645 (detection), §654 (ORDER BY), §660 (timezone.yaml).

## Файлы
- `apps/edge/storage/time_axis.py` (Создание)
- `tests/storage/test_time_axis.py` (Создание)

## Интерфейсы (lean — без кода)
- class TimeAxisService:
  - def compute_official_ts(self, source_ts: datetime, edge_ts: datetime, source_time_quality: str) -> datetime: ...
  - async def detect_clock_shift(self, prev_edge: datetime, new_edge: datetime) -> ClockShift | None: ...
  - async def record_clock_shift(self, shift: ClockShift, events_repo: EventsRepo) -> None: ...
- ClockShift: detected_on, delta, prev_ts, new_ts
- Config: prefer_source_ts, max_skew_sec, backward_jump_sec, forward_jump_sec (default из плана).

## TDD
- **Да:** unit на compute (bad year, skew, prefer), detection (jump back/forward), integration record + event.
- pytest -k "time_axis or clock_shift"

## Подробный процесс выполнения
1. load config из ship-pack/makarov/timezone.yaml (s14).
2. compute: exact logic из плана §631.
3. detect: last_edge_ts watermark в writer; на batch — проверка |Δ| > thresholds.
4. record: insert event 'clock_shift' + row в clock_shift_log; linked_event_id.
5. Не переписывать историю.

## Верификация
- source good + |delta|<300s → official=source (если prefer).
- bad year → official=edge, quality=time_bad.
- jump -70s → event + log row.
- Блокер: s07 (для record), s14 (config).

## Блокеры / CREATIVE
Нет.
