# BACK IMPLEMENT s08-time-axis

## Handoff

- **Статус:** completed
- **Цель:** реализован `TimeAxisService` для вычисления official timestamp, детектирования clock shift и журналирования события со связанной записью.
- **Изменения:**
  - `apps/edge/storage/time_axis.py`: `compute_official_ts`, `detect_clock_shift`, `record_clock_shift`, `ClockShift` и результат с качеством времени.
  - `tests/storage/test_time_axis.py`: targeted unit/integration проверки вычисления времени, порогов сдвига и записи event/log.
- **Проверка:** `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_time_axis.py -k "time_axis or clock_shift"` — 5 passed.
- **Примечание:** для `record_clock_shift` ключ идемпотентности детерминирован, а повторная запись не создаёт orphan `linked_event_id`.
- **Следующий шаг:** BACK IMPLEMENT s09-writer-service.
- **code_changed:** yes
