from datetime import datetime, timedelta, timezone

import pytest

from app.reports.formulas import fuel_flow, fuel_level, round_for_presentation


UTC = timezone.utc


def test_fuel_flow_integrates_flow_rate_in_kg_per_hour() -> None:
    start = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)

    result = fuel_flow(
        (start, start + timedelta(hours=2)),
        [(start, 100, "good"), (start + timedelta(hours=1), 200, "good")],
    )

    assert result.value == pytest.approx(300.0)
    assert result.gaps == []


def test_fuel_flow_excludes_invalid_intervals_and_reports_gaps() -> None:
    start = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)

    result = fuel_flow(
        (start, start + timedelta(hours=2)),
        [(start, 100, "good"), (start + timedelta(hours=1), 200, "stale")],
    )

    assert result.value == pytest.approx(100.0)
    assert result.gaps == [(start + timedelta(hours=1), start + timedelta(hours=2))]


def test_fuel_level_applies_bunkering_and_correction() -> None:
    result = fuel_level(level_start=1000, level_end=700, bunkering_in=50, correction=1.1)

    assert result.value == pytest.approx(385.0)
    assert result.gaps == []


def test_rounding_happens_only_at_presentation_boundary() -> None:
    assert round_for_presentation(12.345, "kg") == 12.3
    assert round_for_presentation(12.35, "kg") == 12.4
    assert round_for_presentation(1.26, "hours") == 1.3
