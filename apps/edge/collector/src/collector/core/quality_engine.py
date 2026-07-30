"""QualityEngine — quality mapping для collector (s11 / CR-COL-04).

Канон правил: `config/quality_rules.yaml` (pydantic `QualityRules`).
Правила редактируются в YAML без правки кода (AC-B4-12). Reload = restart.

Pipeline (s13): RawSample → QualityEngine.evaluate(...) → UnitConverter → TelemetrySample.

AC: AC-B4-04 (5 quality reachable), AC-B4-07 (out-of-range, value kept),
AC-B4-08 (NaN/Inf → bad), AC-B4-12 (YAML rules), AC-B3-06 (StatusCode → Quality).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from collector.config.models import TagMapEntry
from app.telemetry.models import Quality
from collector.domain.raw_models import RawSample

# Приоритет правил: выше = раньше. Порядок = семантика, не configurable.
# quarantine > native_quality > NaN/Inf > range > stale > good
_Q_NIL = Quality.GOOD  # sentinel default


@dataclass(frozen=True)
class EvalResult:
    """Результат evaluate: quality + value encoding + причина-диагностика."""

    quality: Quality
    value: float | int | bool | str | None
    reason: str | None = None


# -----------------------------------------------------------------------------
# Rules schema (pydantic — валидирует YAML при load, fail fast)
# -----------------------------------------------------------------------------


class OpcUaRules(BaseModel):
    severity_class: dict[str, str] = Field(
        default_factory=lambda: {"good": "good", "uncertain": "uncertain", "bad": "bad"}
    )
    overrides: dict[str, str] = Field(
        default_factory=lambda: {
            "GoodClamped": "uncertain",
            "GoodLocalOverride": "uncertain",
            "BadWaitingForInitialData": "stale",
            "BadNoData": "stale",
            "BadNoDataAvailable": "stale",
        }
    )
    unknown_status: str = "uncertain"


class ModbusRules(BaseModel):
    map: dict[str, str] = Field(
        default_factory=lambda: {
            "timeout": "bad",
            "client_error": "bad",
            "exception.1": "bad",
            "exception.2": "bad",
            "exception.3": "bad",
            "exception.4": "bad",
            "exception.5": "uncertain",
            "exception.6": "uncertain",
            "exception.8": "bad",
        }
    )
    unknown_exception: str = "bad"


class ValueRules(BaseModel):
    nan_inf: str = "bad"


class RangeRules(BaseModel):
    out_of_range: str = "uncertain"


class QualityRules(BaseModel):
    version: int = 1
    stale_threshold_sec: float = 3.0
    opcua: OpcUaRules = Field(default_factory=OpcUaRules)
    modbus: ModbusRules = Field(default_factory=ModbusRules)
    value: ValueRules = Field(default_factory=ValueRules)
    range: RangeRules = Field(default_factory=RangeRules)
    unknown_native_quality: str = "good"


# -----------------------------------------------------------------------------
# Standalone mapping helpers (pure, direct use / tests)
# -----------------------------------------------------------------------------


def map_opcua_status(name: str, rules: OpcUaRules) -> Quality:
    """OPC UA StatusCode name → Quality: override → severity-class by name prefix → unknown default.

    name — bare StatusName (без префикса `opcua.`), напр. "Good", "BadNoCommunication".
    """
    if name in rules.overrides:
        return Quality(rules.overrides[name])
    lower = name.lower()
    if lower.startswith("good"):
        return Quality(rules.severity_class.get("good", _Q_NIL))
    if lower.startswith("uncertain"):
        return Quality(rules.severity_class.get("uncertain", _Q_NIL))
    if lower.startswith("bad"):
        return Quality(rules.severity_class.get("bad", _Q_NIL))
    return Quality(rules.unknown_status)


def map_modbus_exception(token: str, rules: ModbusRules) -> Quality:
    """Modbus token → Quality по map, дефолт unknown_exception.

    token — bare token (без префикса `modbus.`), напр. "timeout", "exception.5".
    """
    return Quality(rules.map.get(token, rules.unknown_exception))


# -----------------------------------------------------------------------------
# Engine
# -----------------------------------------------------------------------------


class QualityEngine:
    """Loads quality_rules.yaml once at startup (reload = restart)."""

    def __init__(self, rules: QualityRules) -> None:
        self._rules = rules

    @classmethod
    def from_yaml(cls, path: Path | str) -> "QualityEngine":
        with Path(path).open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(QualityRules.model_validate(data))

    def evaluate(
        self,
        raw: RawSample,
        map_entry: TagMapEntry | None,
        now: datetime,
    ) -> EvalResult:
        """Pure: deterministic по (raw, map_entry, now, self._rules).

        Priority: quarantine > native_quality > NaN/Inf > range > stale > good.
        """
        # 1. quarantine — tag not in map (NormalizerWorker s13 передаёт None)
        if map_entry is None:
            return EvalResult(Quality.QUARANTINE, None, "tag_not_in_map")

        value = raw.raw_value

        # 2. native_quality mapping (OPC Bad / Modbus exception)
        if raw.native_quality is not None:
            nq = self._map_native(raw.native_quality)
            # native non-good short-circuits (bad/uncertain/stale/quarantine wins)
            if nq is not Quality.GOOD:
                return EvalResult(nq, self._encode_value(value, nq), f"native:{raw.native_quality}")

        # 3. NaN/Inf → bad (AC-B4-08)
        if self._is_non_finite(value):
            return EvalResult(Quality(self._rules.value.nan_inf), None, "nan_inf")

        # 4. range → uncertain (AC-B4-07), значение сохраняется
        if self._out_of_range(value, map_entry):
            q = Quality(self._rules.range.out_of_range)
            return EvalResult(q, self._encode_value(value, q), "out_of_range")

        # 5. stale — per-sample age
        age = self._age_sec(raw, now)
        if age is not None and age > self._rules.stale_threshold_sec:
            return EvalResult(Quality.STALE, self._encode_value(value, Quality.STALE), "stale")

        # 6. good
        return EvalResult(Quality.GOOD, value, None)

    # --- internals ---

    def _map_native(self, token: str) -> Quality:
        if token.startswith("opcua."):
            return map_opcua_status(token.removeprefix("opcua."), self._rules.opcua)
        if token.startswith("modbus."):
            return map_modbus_exception(token.removeprefix("modbus."), self._rules.modbus)
        # не распознанный токен без явного правила
        return Quality(self._rules.unknown_native_quality)

    @staticmethod
    def _is_non_finite(value: Any) -> bool:
        return isinstance(value, float) and not math.isfinite(value)

    @staticmethod
    def _out_of_range(value: Any, map_entry: TagMapEntry) -> bool:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        lo, hi = map_entry.range_min, map_entry.range_max
        if lo is not None and value < lo:
            return True
        if hi is not None and value > hi:
            return True
        return False

    @staticmethod
    def _age_sec(raw: RawSample, now: datetime) -> float | None:
        ref = raw.source_ts or raw.recv_ts
        if ref is None:
            return None
        return (now - ref).total_seconds()

    @staticmethod
    def _encode_value(value: Any, quality: Quality) -> float | int | bool | str | None:
        # bad/quarantine → null; uncertain/stale/good → value
        if quality in (Quality.BAD, Quality.QUARANTINE):
            return None
        return value
