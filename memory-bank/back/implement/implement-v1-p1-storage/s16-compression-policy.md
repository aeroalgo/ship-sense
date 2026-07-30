# BACK IMPLEMENT s16 — Compression + retention policy (Alembic 006)

## Реализация
- Создана Alembic-миграция `migrations/versions/006_compression_retention.py` (после s15 / 005_quota_degrade).
- В `upgrade()` включено сжатие на гипертаблице `samples` с параметрами:
  - `timescaledb.compress = true`
  - `timescaledb.compress_segmentby = 'tag_id'`
  - `timescaledb.compress_orderby = 'ts DESC'`
- Добавлены политики TimescaleDB:
  - compression policy: сжатие чанков старше 7 дней (`INTERVAL '7 days'`).
  - retention policy: мягкое удаление чанков старше 1095 дней (3 года, `INTERVAL '1095 days'`).
- В `downgrade()` удалены обе политики (`if_exists => true`) и отключено сжатие на `samples`.

## Верификация
```bash
PYTHONPATH=.:apps/edge/collector/src .venv/bin/alembic upgrade head
PYTHONPATH=.:apps/edge/collector/src .venv/bin/alembic downgrade 005_quota_degrade
```
- Проверено наличие сжатия и политик в системных каталогах TimescaleDB (`_timescaledb_config.bgw_job`).
- Проведена полная проверка rollback-функции (jobs и compression settings удаляются без ошибок).
- Все тесты `tests/storage/` успешно проходят.

**code_changed:** yes

## Статус
completed
