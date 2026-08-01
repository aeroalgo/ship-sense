import json
from pathlib import Path

import pytest

from golden_compare import canonical_body_sha256


FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "reports"


@pytest.mark.t9
@pytest.mark.parametrize(
    "fixture_name",
    (
        "watch_midnight_cross.json",
        "daily_clock_jump.json",
        "fuel_flowmeter_24h.json",
        "daily_gap_midday.json",
    ),
)
def test_golden_fixture_matches_canonical_body_hash(fixture_name: str) -> None:
    fixture = json.loads((FIXTURE_DIR / fixture_name).read_text())

    assert canonical_body_sha256(fixture["body"]) == fixture["expected_body_sha256"]


@pytest.mark.t9
def test_generated_at_is_excluded_from_canonical_body_hash() -> None:
    body = {"generated_at": "2026-07-31T00:00:00Z", "value": 42}

    assert canonical_body_sha256(body) == canonical_body_sha256(
        {"generated_at": "2026-08-01T00:00:00Z", "value": 42}
    )
