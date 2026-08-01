from datetime import datetime, timedelta, timezone

from apps.edge.ota.healthcheck import HealthSignal, HealthStatus, evaluate_health


def test_health_requires_fresh_sample_api_and_database_for_three_passes() -> None:
    now = datetime.now(timezone.utc)
    signals = [
        HealthSignal("collector", "pass"),
        HealthSignal("api", "pass"),
        HealthSignal("database", "pass"),
    ]

    first = evaluate_health(
        HealthStatus(last_sample_at=now - timedelta(seconds=10), signals=signals),
        now=now,
        consecutive_passes=0,
    )
    final = evaluate_health(
        HealthStatus(last_sample_at=now - timedelta(seconds=10), signals=signals),
        now=now,
        consecutive_passes=2,
    )

    assert first.consecutive_passes == 1
    assert first.ready is False
    assert final.consecutive_passes == 3
    assert final.ready is True


def test_health_is_fail_closed_for_stale_or_unknown_signal() -> None:
    now = datetime.now(timezone.utc)
    result = evaluate_health(
        HealthStatus(
            last_sample_at=now - timedelta(seconds=60),
            signals=[HealthSignal("collector", "pass"), HealthSignal("api", "unknown")],
        ),
        now=now,
        consecutive_passes=2,
    )

    assert result.ready is False
    assert result.consecutive_passes == 0
    assert result.code in {"STALE_SAMPLE", "HEALTH_UNKNOWN"}
