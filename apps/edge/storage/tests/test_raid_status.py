import json

from apps.edge.storage.raid.status import RaidHealth, parse_zpool_status


def test_zpool_status_maps_online_and_resilvering() -> None:
    online = parse_zpool_status(json.dumps({"state": "ONLINE", "scan": {"state": "none"}}))
    rebuilding = parse_zpool_status(json.dumps({"state": "ONLINE", "scan": {"state": "resilvering"}}))

    assert online.health == RaidHealth.ONLINE
    assert online.degraded is False
    assert rebuilding.health == RaidHealth.RESILVERING
    assert rebuilding.degraded is True
    assert rebuilding.resilvering is True


def test_zpool_status_fails_closed_for_invalid_or_degraded_output() -> None:
    assert parse_zpool_status("not json").health == RaidHealth.UNKNOWN
    degraded = parse_zpool_status(json.dumps({"state": "DEGRADED"}))

    assert degraded.degraded is True
    assert degraded.health == RaidHealth.DEGRADED
