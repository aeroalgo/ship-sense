from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


BASELINE_TAGS = (
    "TAI4101", "TAI4102", "TAI4202", "TAI4204", "TAI4205", "TAI4207", "TAI4208",
    "TAI4210", "TAI4211", "TAI4213", "TAI4214", "TAI4216", "TAI4217", "TAI4219",
    "TAI4220", "TAI4222", "TAI4223", "TAI4225", "TAI4226", "TAI4228", "TAI4229",
    "TAI4231", "TAI4232", "TAI4234", "TAI4235", "TAI4237", "TAI4238", "TAI4240",
    "TAI4241", "TAI4243", "TAI4244", "TAI4246", "TAI4247", "TAI4249", "TAI4250",
    "TAI4252", "TAI4253", "TAI4255", "TAI4256", "TAI4258", "TAI4259", "TAI4261",
    "TAI4262", "TAI4264", "TAI4265", "TAI4267", "TAI4268", "TAI4270", "TAI4271",
    "TAI4273", "TAI4274", "TAI4276", "SKT002",
)


@dataclass(frozen=True)
class ModeFilter:
    rpm_tag: str = "SKT001"
    rpm_min: float = 10.0


@dataclass(frozen=True)
class WarningTagConfig:
    tag_id: str
    setpoint_source: str = "aps"
    setpoint_value: float | None = None
    unit: str | None = None
    threshold_pct: float = 0.9
    ewma_window_hours: float = 24.0
    min_trend_len_hours: float = 6.0
    r2_min: float = 0.6
    hysteresis_pct: float = 0.02
    startup_guard_sec: float = 300.0
    comparison: str = "high"
    mode_filter: ModeFilter = ModeFilter()


@dataclass(frozen=True)
class WarningConfig:
    version: str
    tags: tuple[WarningTagConfig, ...]


def load_warning_config(path: Path | str, known_tags: set[str]) -> WarningConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or raw.get("version") != "1":
        raise ValueError("warnings config version must be '1'")
    defaults = raw.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError("warnings defaults must be a mapping")
    raw_tags = raw.get("tags")
    if not isinstance(raw_tags, list) or not raw_tags:
        raise ValueError("warnings tags must be a non-empty list")
    seen: set[str] = set()
    configs: list[WarningTagConfig] = []
    for item in raw_tags:
        if not isinstance(item, dict):
            raise ValueError("warning tag entries must be mappings")
        tag_id = str(item.get("tag_id", ""))
        if not tag_id or tag_id in seen:
            raise ValueError(f"duplicate or missing warning tag: {tag_id}")
        if tag_id not in known_tags:
            raise ValueError(f"unknown warning tag: {tag_id}")
        seen.add(tag_id)
        mode_data = item.get("mode_filter", defaults.get("mode_filter", {})) or {}
        if not isinstance(mode_data, dict):
            raise ValueError(f"mode_filter must be a mapping: {tag_id}")
        values: dict[str, Any] = {**defaults, **item}
        configs.append(WarningTagConfig(
            tag_id=tag_id,
            setpoint_source=str(values.get("setpoint_source", "aps")),
            setpoint_value=(float(values["setpoint_value"]) if values.get("setpoint_value") is not None else None),
            unit=(str(values["unit"]) if values.get("unit") is not None else None),
            threshold_pct=float(values.get("threshold_pct", 0.9)),
            ewma_window_hours=float(values.get("ewma_window_hours", 24)),
            min_trend_len_hours=float(values.get("min_trend_len_hours", 6)),
            r2_min=float(values.get("r2_min", 0.6)),
            hysteresis_pct=float(values.get("hysteresis_pct", 0.02)),
            startup_guard_sec=float(values.get("startup_guard_sec", 300)),
            comparison=str(values.get("comparison", "high")),
            mode_filter=ModeFilter(str(mode_data.get("rpm_tag", "SKT001")), float(mode_data.get("rpm_min", 10))),
        ))
    return WarningConfig(version="1", tags=tuple(configs))
