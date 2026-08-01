from apps.edge.storage.health import StorageHealth, reduce_storage_health
from apps.edge.storage.raid.status import RaidHealth, RaidSnapshot


def test_storage_health_uses_inclusive_disk_threshold_and_fail_closed_unknown() -> None:
    healthy = reduce_storage_health(79.9, RaidSnapshot("shipsense", "online", False, False, RaidHealth.ONLINE), True, 1.0)
    warning = reduce_storage_health(80.0, RaidSnapshot("shipsense", "online", False, False, RaidHealth.ONLINE), True, 1.0)
    unknown = reduce_storage_health(None, RaidSnapshot("shipsense", "unknown", True, False, RaidHealth.UNKNOWN), None, None)

    assert healthy.disk_warning is False
    assert warning.disk_warning is True
    assert "storage.disk_high" in warning.reason_codes
    assert unknown.overall_healthy is False
    assert unknown.backup_last_ok is False
    assert "storage.raid_unknown" in unknown.reason_codes
