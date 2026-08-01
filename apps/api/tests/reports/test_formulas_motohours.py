from datetime import datetime, timedelta, timezone

import pytest

from app.reports.formulas import FormulaLoader, load_formulas, motohours, peak, tw_avg


UTC = timezone.utc


def test_motohours_integrates_running_intervals_and_records_quality_gaps() -> None:
    start = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
    end = start + timedelta(hours=4)
    result = motohours(
        (start, end),
        [
            (start, True, "good"),
            (start + timedelta(hours=1), True, "good"),
            (start + timedelta(hours=2), False, "stale"),
            (start + timedelta(hours=3), True, "good"),
        ],
    )

    assert result.value == pytest.approx(3.0)
    assert result.gaps == [(start + timedelta(hours=2), start + timedelta(hours=3))]


def test_time_weighted_average_and_peak_use_valid_intervals() -> None:
    start = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
    result = tw_avg(
        (start, start + timedelta(hours=3)),
        [
            (start, 10, "good"),
            (start + timedelta(hours=1), 20, "good"),
            (start + timedelta(hours=2), 30, "bad"),
        ],
    )

    assert result.value == pytest.approx(15.0)
    assert peak((start, start + timedelta(hours=3)), [(start, 10, "good"), (start + timedelta(hours=1), 20, "good")]).value == 20


def test_formula_loader_reads_versioned_ship_pack() -> None:
    formulas = load_formulas("latest")

    assert formulas.manifest.version == "v1"
    assert formulas.config.min_running_duration_sec == 30
    assert formulas.config.fuel_unit == "kg"
    assert isinstance(FormulaLoader().load("v1"), type(formulas))
