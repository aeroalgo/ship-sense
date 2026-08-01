from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from scripts.soak.assert_pass_criteria import assert_pass_criteria
from scripts.soak.scrape_metrics import MetricSnapshot, parse_prometheus

pytestmark = pytest.mark.slow


def test_parse_prometheus_extracts_t1_metrics() -> None:
    payload = """
    process_resident_memory_bytes 104857600
    shipsense_write_latency_seconds{quantile="0.99"} 0.25
    shipsense_disk_used_ratio 0.71
    shipsense_ws_connections 4
    """

    snapshot = parse_prometheus(payload, timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc))

    assert snapshot.rss_bytes == 104857600
    assert snapshot.write_latency_p99_seconds == 0.25
    assert snapshot.disk_used_ratio == 0.71
    assert snapshot.ws_connections == 4


def test_assert_pass_criteria_accepts_bounded_fragment() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    snapshots = [
        MetricSnapshot(
            timestamp=start,
            rss_bytes=100_000_000,
            write_latency_p99_seconds=0.2,
            disk_used_ratio=0.70,
            ws_connections=2,
        ),
        MetricSnapshot(
            timestamp=start + timedelta(hours=12),
            rss_bytes=100_400_000,
            write_latency_p99_seconds=0.3,
            disk_used_ratio=0.72,
            ws_connections=3,
        ),
    ]

    result = assert_pass_criteria(snapshots, max_memory_slope_percent_per_day=1.0)

    assert result.passed
    assert result.memory_slope_percent_per_day < 1.0
    assert result.write_latency_p99_seconds == 0.3


def test_assert_pass_criteria_rejects_memory_leak() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    snapshots = [
        MetricSnapshot(timestamp=start, rss_bytes=100, ws_connections=1),
        MetricSnapshot(
            timestamp=start + timedelta(days=1),
            rss_bytes=103,
            ws_connections=1,
        ),
    ]

    result = assert_pass_criteria(snapshots, max_memory_slope_percent_per_day=1.0)

    assert not result.passed
    assert "memory_slope" in result.failures
