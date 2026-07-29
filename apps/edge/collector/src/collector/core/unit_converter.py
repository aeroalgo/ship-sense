"""UnitConverter — scale/offset + справочник conversions (s12 / AC-B4-03, AC-B4-09).

Канон правил: `config/units.yaml` (pydantic `UnitRules`).
Правила редактируются в YAML без правки кода. Reload = restart.

Два уровня применения:
  1. Per-tag scale/offset из TagMapEntry — калибровка raw→engineering
     (plan §14.3 per-tag override). Если scale/offset заданы, conversion-словарь
     пропускается: калибровка уже даёт целевую единицу.
  2. Conversion-словарь — lookup (from, to); нет правила → AC-B4-09:
     unit="unknown" + warning log, value passed through без изменения.

Pipeline (s13): QualityEngine.evaluate(...) → UnitConverter.convert(...) → TelemetrySample.unit.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger("collector.core.unit_converter")

UNKNOWN = "unknown"


class ConversionRule(BaseModel):
    """value_out = scale * value_in + offset."""

    # `from` зарезервировано → поле from_ с alias
    from_: str = Field(alias="from")
    to: str
    scale: float = 1.0
    offset: float = 0.0

    model_config = {"populate_by_name": True}


class UnitRules(BaseModel):
    aliases: dict[str, str] = Field(default_factory=dict)
    conversions: list[ConversionRule] = Field(default_factory=list)


class UnitConverter:
    """Loads units.yaml once at startup (reload = restart)."""

    def __init__(self, rules: UnitRules) -> None:
        self._rules = rules
        # (from_canonical, to_canonical) → rule
        self._table: dict[tuple[str, str], ConversionRule] = {
            (r.from_, r.to): r for r in rules.conversions
        }

    @classmethod
    def from_yaml(cls, path: Path | str) -> "UnitConverter":
        with Path(path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(UnitRules.model_validate(data))

    def convert(
        self,
        value: Any,
        from_unit: str | None,
        to_unit: str | None,
        scale: float | None = None,
        offset: float | None = None,
    ) -> tuple[Any, str]:
        """Конвертация значения.

        - non-numeric (None/bool/str/NaN) → passthrough, unit = resolved to_unit.
        - per-tag scale/offset заданы → калибровка raw→engineering, to_unit.
        - иначе conversion-словарь; нет правила → AC-B4-09.
        """
        src = self._resolve(from_unit)
        dst = self._resolve(to_unit)

        if not _is_numeric(value):
            return value, dst or from_unit or UNKNOWN

        if scale is not None or offset is not None:
            s = 1.0 if scale is None else float(scale)
            o = 0.0 if offset is None else float(offset)
            return s * value + o, dst or to_unit or UNKNOWN

        if src == dst:
            return value, dst or from_unit or UNKNOWN

        rule = self._table.get((src, dst))
        if rule is None:
            logger.warning(
                "No unit conversion rule: %r → %r; passing value through as unit=unknown",
                from_unit,
                to_unit,
            )
            return value, UNKNOWN
        return rule.scale * value + rule.offset, dst

    def _resolve(self, unit: str | None) -> str:
        if not unit:
            return ""
        return self._rules.aliases.get(unit, unit)


def _is_numeric(value: Any) -> bool:
    """int/float, но НЕ bool. NaN/Inf числовые ( QualityEngine их помечает bad)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)
