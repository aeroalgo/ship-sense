from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.edge.storage.backup.coordinator import BackupCoordinator, RestoreStatus, verify_restore
from apps.edge.storage.quota_manager import DiskUsage, QuotaManager, QuotaSettings
from apps.edge.storage.raid.status import RaidHealth, parse_zpool_status


@pytest.mark.asyncio
async def test_yanked_disk_alerts_and_degrades_without_touching_events() -> None:
    session = _AsyncSession()
    manager = QuotaManager(session, settings=QuotaSettings(alert_pct=80, samples_quota_bytes=100))
    manager._disk_usage = _async_value(DiskUsage(1000, 850, 0))
    manager._samples_size = _async_value(250)
    manager._oldest_chunks = _async_value([("chunk-1", 100), ("chunk-2", 150)])
    manager._drop_chunk = _async_value(None)

    result = await manager.check_and_degrade()

    assert result.alerted is True
    assert result.degraded_chunks == 2
    assert result.bytes_freed == 250
    sql = " ".join(str(call[0]) for call in session.calls)
    assert "samples_degrade_log" in sql
    assert "events" not in sql.lower()


def test_zip_disk_starts_resilvering() -> None:
    snapshot = parse_zpool_status(
        json.dumps({"state": "DEGRADED", "scan": {"state": "resilvering"}})
    )

    assert snapshot.degraded is True
    assert snapshot.resilvering is True
    assert snapshot.health == RaidHealth.RESILVERING


def test_restore_events_backup_matches_manifest_row_payload(tmp_path: Path) -> None:
    events = b"COPY events FROM stdin;\n1\talpha\n2\tbeta\n\\.\n"
    backup = BackupCoordinator(tmp_path).publish(
        {"events.sql": events, "ship-pack/config.yaml": b"vessel: makarov\n"},
        events_row_count=2,
    )

    restored = verify_restore(backup.path)

    assert restored.status is RestoreStatus.PASSED
    assert (backup.path / "events.sql").read_bytes().count(b"\n") == 4
    manifest = json.loads((backup.path / "manifest.json").read_text())
    assert manifest["events_row_count"] == 2


def _async_value(value):
    async def getter(*args, **kwargs):
        return value

    return getter


class _AsyncSession:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    async def execute(self, *args, **kwargs):
        self.calls.append(args)


@pytest.fixture
async def _unused_fixture():
    yield
