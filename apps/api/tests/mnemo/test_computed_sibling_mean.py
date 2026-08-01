import math

from app.mnemo.computed import sibling_mean_delta


def test_sibling_mean_delta_returns_target_deviation() -> None:
    result = sibling_mean_delta(110, {"a": 100, "b": 120})

    assert result.value == 0
    assert result.status == "ok"


def test_quarantined_and_missing_values_are_unknown_not_zero() -> None:
    result = sibling_mean_delta(
        110,
        {"a": None, "b": 100},
        quarantined=frozenset({"b"}),
    )

    assert result.value is None
    assert result.status == "unknown"


def test_non_numeric_and_bool_inputs_are_excluded() -> None:
    result = sibling_mean_delta(110, {"a": True, "b": "100"})

    assert result.value is None
    assert result.status == "unknown"
    assert math.isfinite(result.value) if result.value is not None else True
