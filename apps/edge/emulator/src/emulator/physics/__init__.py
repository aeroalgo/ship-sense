"""Pure physics helpers used by the signal model."""

from emulator.physics.correlations import correlate, correlate_rpm_temp_pressure
from emulator.physics.daily_patterns import daily_factor

__all__ = ["correlate", "correlate_rpm_temp_pressure", "daily_factor"]
