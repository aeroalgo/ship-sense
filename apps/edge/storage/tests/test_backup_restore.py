from datetime import datetime, timezone
from pathlib import Path

from apps.edge.storage.backup.coordinator import BackupCoordinator, RestoreStatus, verify_restore


def test_backup_publishes_manifest_hashes_and_complete(tmp_path: Path) -> None:
    coordinator = BackupCoordinator(tmp_path)

    result = coordinator.publish(
        {
            "events.sql": b"COPY events FROM stdin;\n1\talpha\n\\.\n",
            "ship-pack/config.yaml": b"vessel: makarov\n",
            "ship-pack/formulas.yaml": b"motohours: 1\n",
            "ship-pack/warnings.yaml": b"[]\n",
        },
        created_at=datetime(2026, 7, 31, tzinfo=timezone.utc),
        events_row_count=1,
    )

    assert result.path.exists()
    assert (result.path / "COMPLETE").read_text() == ""
    assert result.manifest.files["events.sql"].sha256
    assert verify_restore(result.path).status is RestoreStatus.PASSED


def test_failed_payload_does_not_publish_complete(tmp_path: Path) -> None:
    coordinator = BackupCoordinator(tmp_path)

    try:
        coordinator.publish({"events.sql": b"ok", "ship-pack/config.yaml": None})
    except TypeError:
        pass

    assert not list(tmp_path.glob("**/COMPLETE"))


def test_complete_backup_is_not_overwritten(tmp_path: Path) -> None:
    coordinator = BackupCoordinator(tmp_path)
    first = coordinator.publish({"events.sql": b"first"}, created_at=datetime(2026, 7, 31, tzinfo=timezone.utc))
    second = coordinator.publish({"events.sql": b"second"}, created_at=datetime(2026, 7, 31, tzinfo=timezone.utc))

    assert first.path != second.path
    assert (first.path / "events.sql").read_bytes() == b"first"
    assert (second.path / "events.sql").read_bytes() == b"second"


def test_restore_detects_checksum_failure(tmp_path: Path) -> None:
    result = BackupCoordinator(tmp_path).publish({"events.sql": b"events"})
    (result.path / "events.sql").write_bytes(b"tampered")

    checked = verify_restore(result.path)

    assert checked.status is RestoreStatus.FAILED
    assert checked.code == "checksum_mismatch"
