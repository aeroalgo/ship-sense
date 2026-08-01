from datetime import datetime, timedelta, timezone

import pytest

from app.warnings.engine import DriftEngine, DriftSample, WarningState
from app.warnings.math import drift_rate, eta_days, ewma_update


UTC = timezone.utc


def test_ewma_uses_elapsed_time_not_sample_count() -> None:
    first = datetime(2026, 1, 1, tzinfo=UTC)
    state = ewma_update(None, 10.0, first, tau=10.0)
    state = ewma_update(state, 20.0, first + timedelta(seconds=10), tau=10.0)

    assert state.value == pytest.approx(16.321205588)


def test_ewma_rejects_time_travel_and_zero_dt_is_idempotent() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    state = ewma_update(None, 10.0, timestamp, tau=60.0)
    assert ewma_update(state, 20.0, timestamp, tau=60.0) == state
    with pytest.raises(ValueError, match="timestamp"):
        ewma_update(state, 20.0, timestamp - timedelta(seconds=1), tau=60.0)


def test_eta_is_only_returned_for_positive_stable_drift() -> None:
    assert eta_days(80.0, 90.0, 10.0) == pytest.approx(1.0 / 24.0)
    assert eta_days(80.0, 90.0, 0.0) is None
    assert eta_days(95.0, 90.0, 10.0) is None
    assert drift_rate([(0.0, 10.0), (1.0, 20.0)]) == pytest.approx(10.0)


def test_engine_enters_and_exits_with_hysteresis() -> None:
    engine = DriftEngine(
        tag_id="TAI4101",
        setpoint=100.0,
        threshold_pct=0.9,
        hysteresis_pct=0.05,
        ewma_window_hours=0.001,
        min_trend_len=2,
        startup_guard_sec=0,
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    assert engine.process(DriftSample(start, 80.0, rpm=20.0)).state is WarningState.CLEAR
    entered = engine.process(DriftSample(start + timedelta(hours=1), 95.0, rpm=20.0))
    assert entered.state is WarningState.ACTIVE
    held = engine.process(DriftSample(start + timedelta(hours=2), 88.0, rpm=20.0))
    assert held.state is WarningState.ACTIVE
    exited = engine.process(DriftSample(start + timedelta(hours=3), 80.0, rpm=20.0))
    assert exited.state is WarningState.CLEAR


def test_engine_suppresses_startup_and_low_rpm() -> None:
    engine = DriftEngine(
        tag_id="TAI4101",
        setpoint=100.0,
        startup_guard_sec=300,
        rpm_min=10.0,
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    result = engine.process(DriftSample(start, 99.0, rpm=0.0))
    assert result.state is WarningState.SUPPRESSED
    result = engine.process(DriftSample(start + timedelta(seconds=1), 99.0, rpm=20.0))
    assert result.state is WarningState.SUPPRESSED
    result = engine.process(DriftSample(start + timedelta(seconds=301), 99.0, rpm=20.0))
    assert result.state is WarningState.ACTIVE
    assert result.suppressed_reason is None
