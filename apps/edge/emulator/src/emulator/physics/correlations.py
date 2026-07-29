from __future__ import annotations

from collections.abc import Mapping, Sequence


def correlate(
    drivers: Mapping[str, float],
    coefficients: Mapping[str, float],
    baseline: float,
    noise: float = 0.0,
    noise_sample: float = 0.0,
) -> float:
    """Combine driver deltas with a deterministic noise sample."""
    value = baseline + sum(drivers[name] * coefficient for name, coefficient in coefficients.items())
    return value + noise * noise_sample


def correlate_rpm_temp_pressure(
    rpm: float,
    baseline_temperature: float,
    baseline_pressure: float,
    *,
    temperature_coeff: float = 0.15,
    pressure_coeff: float = 0.005,
    reference_rpm: float = 0.0,
    noise: float = 0.0,
    noise_sample: float = 0.0,
) -> dict[str, float]:
    """Return a small, readable RPM → temperature/pressure preset."""
    delta = rpm - reference_rpm
    values = {
        "temperature": correlate(
            {"rpm": delta}, {"rpm": temperature_coeff}, baseline_temperature, noise, noise_sample
        ),
        "pressure": correlate(
            {"rpm": delta}, {"rpm": pressure_coeff}, baseline_pressure, noise, noise_sample
        ),
    }
    return values
