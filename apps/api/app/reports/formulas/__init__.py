from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Literal, TypeAlias

import yaml


Quality: TypeAlias = Literal["good"] | str
Interval: TypeAlias = tuple[datetime, datetime]
Sample: TypeAlias = tuple[datetime, float | bool, Quality]


@dataclass(frozen=True)
class FormulaResult:
    value: float
    gaps: list[Interval]


@dataclass(frozen=True)
class FormulaConfig:
    fuel_unit: str
    fuel_rule: str
    hours_precision: float
    min_running_duration_sec: int
    debounce_window_sec: int


@dataclass(frozen=True)
class FormulaManifest:
    version: str
    vessel: str
    formulas: dict[str, str]


@dataclass(frozen=True)
class FormulaPack:
    manifest: FormulaManifest
    config: FormulaConfig


_DEFAULT_ROOT = Path(__file__).resolve().parents[5] / "ship-pack" / "makarov" / "formulas"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except OSError as exc:
        raise RuntimeError(f"Unable to read formula file: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Formula file must contain a mapping: {path}")
    return data


def _validate_version(version: str) -> None:
    if version != "v1":
        raise ValueError(f"Unsupported formulas version: {version}")


class FormulaLoader:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or _DEFAULT_ROOT

    def load(self, version: str = "latest") -> FormulaPack:
        manifest_data = _load_yaml(self._root / "manifest.yaml")
        manifest = FormulaManifest(
            version=str(manifest_data.get("version", "")),
            vessel=str(manifest_data.get("vessel", "")),
            formulas=dict(manifest_data.get("formulas", {})),
        )
        selected = manifest.version if version == "latest" else version
        _validate_version(selected)
        if selected != manifest.version:
            raise ValueError(f"Formula version is not available: {version}")
        rounding = _load_yaml(self._root / selected / "rounding.yaml")
        running = _load_yaml(self._root / selected / "motohours.yaml").get("running", {})
        debounce = _load_yaml(self._root / selected / "debounce.yaml")
        return FormulaPack(
            manifest=manifest,
            config=FormulaConfig(
                fuel_unit=str(rounding.get("fuel_unit", "kg")),
                fuel_rule=str(rounding.get("fuel_rule", "half_up")),
                hours_precision=float(rounding.get("hours_precision", 0.1)),
                min_running_duration_sec=int(running.get("min_running_duration_sec", debounce.get("min_running_duration_sec", 0))),
                debounce_window_sec=int(debounce.get("debounce_window_sec", 0)),
            ),
        )


def load_formulas(version: str = "latest") -> FormulaPack:
    return FormulaLoader().load(version)


def _intervals(samples: Iterable[Sample], period: Interval) -> Iterable[tuple[datetime, datetime, float | bool, Quality]]:
    start, end = period
    ordered = sorted(samples, key=lambda item: item[0])
    for index, (timestamp, value, quality) in enumerate(ordered):
        next_timestamp = ordered[index + 1][0] if index + 1 < len(ordered) else end
        segment_start = max(timestamp, start)
        segment_end = min(next_timestamp, end)
        if segment_start < segment_end:
            yield segment_start, segment_end, value, quality


def _valid_segments(samples: Iterable[Sample], period: Interval) -> tuple[list[tuple[datetime, datetime, float | bool]], list[Interval]]:
    valid: list[tuple[datetime, datetime, float | bool]] = []
    gaps: list[Interval] = []
    for segment_start, segment_end, value, quality in _intervals(samples, period):
        if quality == "good":
            valid.append((segment_start, segment_end, value))
        else:
            gaps.append((segment_start, segment_end))
    return valid, gaps


def motohours(period: Interval, running_series: Iterable[Sample]) -> FormulaResult:
    valid, gaps = _valid_segments(running_series, period)
    seconds = sum((end - start).total_seconds() for start, end, value in valid if bool(value))
    return FormulaResult(value=seconds / 3600, gaps=gaps)


def tw_avg(period: Interval, series: Iterable[Sample]) -> FormulaResult:
    valid, gaps = _valid_segments(series, period)
    duration = sum((end - start).total_seconds() for start, end, _ in valid)
    if not duration:
        raise ValueError("No valid intervals available for time-weighted average")
    weighted = sum(float(value) * (end - start).total_seconds() for start, end, value in valid)
    return FormulaResult(value=weighted / duration, gaps=gaps)


def peak(period: Interval, series: Iterable[Sample]) -> FormulaResult:
    valid, gaps = _valid_segments(series, period)
    if not valid:
        raise ValueError("No valid intervals available for peak")
    return FormulaResult(value=max(float(value) for _, _, value in valid), gaps=gaps)


def fuel_flow(period: Interval, series: Iterable[Sample]) -> FormulaResult:
    valid, gaps = _valid_segments(series, period)
    total = sum(float(value) * (end - start).total_seconds() / 3600 for start, end, value in valid)
    return FormulaResult(value=total, gaps=gaps)


def fuel_level(*, level_start: float, level_end: float, bunkering_in: float = 0, correction: float = 1.0) -> FormulaResult:
    if correction < 0:
        raise ValueError("Fuel correction must not be negative")
    return FormulaResult(value=(level_start - level_end + bunkering_in) * correction, gaps=[])


def round_for_presentation(value: float, unit: Literal["kg", "hours"]) -> float:
    precision = Decimal("0.1")
    return float(Decimal(str(value)).quantize(precision, rounding=ROUND_HALF_UP))
