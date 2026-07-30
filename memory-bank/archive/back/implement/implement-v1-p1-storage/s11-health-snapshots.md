# BACK IMPLEMENT s11 — HealthSnapshot loop

## Реализация

- Добавлен `HealthSnapshotService` с фоновым 60-секундным loop и graceful stop.
- `snapshot_once` собирает disk/ram/cpu через psutil, размеры `samples` и `events` через PostgreSQL, сохраняет `health_snapshots`, принимает `queue_depth` и `extra`.
- При загрузке диска от 80% добавляется `extra.alert = "disk_80"`.
- Добавлен structured log `storage.health.snapshot`.

## Верификация

`PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_health_snapshot.py -q` — 2 passed.

## Статус

completed
