from datetime import datetime, timedelta, timezone

import pytest

from app.semantic.models import SignalType
from app.telemetry.service import _downsample, pick_resolution


class Row:
    def __init__(self, timestamp: datetime, value: float | None, quality: int) -> None:
        self.official_ts = timestamp
        self.value = value
        self.quality = quality


def test_downsample_omits_gaps_and_keeps_worst_quality() -> None:
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    rows = [
        Row(start + timedelta(seconds=1), 10.0, 0),
        Row(start + timedelta(seconds=2), 20.0, 4),
        Row(start + timedelta(seconds=121), 30.0, 0),
    ]

    points = _downsample(rows, start, "1m", SignalType.ANALOG)

    assert [point.samples for point in points] == [2, 1]
    assert points[0].quality == "quarantine"
    assert points[0].value == 15.0
    assert points[0].min == 10.0
    assert points[0].max == 20.0


def test_downsample_uses_last_for_boolean_tags() -> None:
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    rows = [
        Row(start + timedelta(seconds=1), 0.0, 0),
        Row(start + timedelta(seconds=2), 1.0, 0),
    ]

    points = _downsample(rows, start, "1m", SignalType.DIGITAL)

    assert points[0].value == 1.0
    assert points[0].samples == 2


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (1500, "raw"),
        (1501, "2s"),
        (7_200, "5s"),
        (86_400, "1m"),
        (604_800, "10m"),
    ],
)
def test_pick_resolution_targets_series_budget(seconds: int, expected: str) -> None:
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    assert pick_resolution(start, start + timedelta(seconds=seconds)) == expected


def test_pick_resolution_rejects_reverse_window() -> None:
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="to must be greater than from"):
        pick_resolution(start, start)
