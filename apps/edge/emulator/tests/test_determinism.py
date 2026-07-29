from __future__ import annotations

from pathlib import Path

import pytest

from emulator.physics.correlations import correlate_rpm_temp_pressure
from emulator.physics.daily_patterns import daily_factor
from emulator.tag_model import TagGenerator, load_profile


PROFILE_PATH = Path(__file__).parents[1] / "config" / "tags_stub.yaml"


def test_stub_profile_contains_586_signals() -> None:
    profile = load_profile(PROFILE_PATH)

    assert len(profile["signals"]) == 586
    native_ids = [native_id for signal in profile["signals"] for native_id in signal["native_ids"].values()]
    assert len(native_ids) == len(set(native_ids))


def test_same_seed_replays_same_snapshots() -> None:
    profile = load_profile(PROFILE_PATH)
    left = TagGenerator(seed=42, profile=profile)
    right = TagGenerator(seed=42, profile=profile)

    assert [left.tick(t) for t in range(5)] == [right.tick(t) for t in range(5)]


def test_signal_noise_stream_does_not_depend_on_profile_order() -> None:
    profile = load_profile(PROFILE_PATH)
    reordered = {**profile, "signals": list(reversed(profile["signals"]))}
    left = TagGenerator(seed=42, profile=profile)
    right = TagGenerator(seed=42, profile=reordered)

    assert left.tick(3) == right.tick(3)


def test_rpm_temperature_pressure_correlation_is_positive() -> None:
    low = correlate_rpm_temp_pressure(1000, 60, 2, noise_sample=0)
    high = correlate_rpm_temp_pressure(3000, 60, 2, noise_sample=0)

    assert high["temperature"] > low["temperature"]
    assert high["pressure"] > low["pressure"]


def test_daily_factor_is_bounded_and_periodic() -> None:
    assert daily_factor(0) == pytest.approx(daily_factor(24 * 60 * 60))
    assert 0.0 <= daily_factor(12 * 60 * 60) <= 1.0
