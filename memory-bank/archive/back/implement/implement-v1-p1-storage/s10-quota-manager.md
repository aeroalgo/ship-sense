# BACK IMPLEMENT s10 — QuotaManager

## Result

- Реализован `apps/edge/storage/quota_manager.py`: сбор disk/Postgres usage, threshold alert, samples-only chunk degradation и watermark update.
- Добавлены targeted tests в `tests/storage/test_quota_degrade.py`.

## Verification

`PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_quota_degrade.py -q` — **2 passed**.

## Notes

- `QuotaManager` получает `AsyncSession` и `QuotaSettings` через конструктор.
- Degrade ограничен hypertable `samples`; SQL не обращается к `events`.
