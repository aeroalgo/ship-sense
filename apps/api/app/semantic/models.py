"""Pydantic v2 models for the ship-pack semantic layer (s12).

Mirror of `ship-pack/makarov/*.yaml` (plan §677–778). No DB code here —
pure validated data + in-memory tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class SignalType(StrEnum):
    ANALOG = "analog"
    ALARM_BIT = "alarm_bit"
    DIGITAL = "digital"
    COUNTER = "counter"


class AlarmClass(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AssetNodeKind(StrEnum):
    VESSEL = "vessel"
    ENGINE_ROOM = "engine_room"
    SYSTEM = "system"
    MECHANISM = "mechanism"


# --------------------------------------------------------------------------- #
# CR-STO-03: display states and quarantine (s13)
# --------------------------------------------------------------------------- #

class TagDisplayState(StrEnum):
    """Per-tag UI state per creative CR-STO-03 precedence (top first)."""

    STOP = "stop"
    QUARANTINE = "quarantine"
    NO_DATA = "no_data"
    STALE = "stale"
    NORMAL = "normal"


class AggregateStatus(StrEnum):
    """Worst-of aggregate for tree nodes (critical > warning > quarantine > no_data > normal)."""

    CRITICAL = "critical"
    WARNING = "warning"
    QUARANTINE = "quarantine"
    NO_DATA = "no_data"
    NORMAL = "normal"


class QuarantineKind(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True, slots=True)
class QuarantineEntry:
    """One diff entry for native map diff result."""

    tag_id: str
    native_id: str | None = None
    reason: str = ""
    kind: QuarantineKind = QuarantineKind.ADDED


@dataclass(frozen=True, slots=True)
class QuarantineReport:
    """Result of diff_native_map vs approved pack native_map."""

    added: list[QuarantineEntry] = field(default_factory=list)
    removed: list[QuarantineEntry] = field(default_factory=list)
    changed: list[QuarantineEntry] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# vessel.yaml
# --------------------------------------------------------------------------- #

class VesselDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    imo: str | None = None
    pack_version: str


class SourceDef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str | None = None
    tag_count_expected: int = Field(..., ge=0)


# --------------------------------------------------------------------------- #
# assets.yaml tree nodes
# --------------------------------------------------------------------------- #

class MechanismNode(BaseModel):
    """Leaf asset node carrying the actual tags list."""
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str | None = None
    tags: list[str] = Field(default_factory=list)


class SystemNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str | None = None
    mechanisms: list[MechanismNode] = Field(default_factory=list)


class EngineRoomNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str | None = None
    systems: list[SystemNode] = Field(default_factory=list)


class AssetNode(BaseModel):
    """Generic polymorphic tree node (post-build flattened from YAML)."""
    model_config = ConfigDict(extra="forbid")
    kind: AssetNodeKind
    id: str
    label: str | None = None
    children: list["AssetNode"] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


AssetNode.model_rebuild()

# Alias for the vessel-root flavour used by SemanticPack
SemanticMetaNode = AssetNode


# --------------------------------------------------------------------------- #
# tag_map.yaml
# --------------------------------------------------------------------------- #

class TagRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min: float
    max: float


class TagSetpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    warn: float | None = None
    alarm: float | None = None


class TagMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str | None = None
    unit: str
    source_id: str
    signal_type: SignalType
    range: TagRange | None = None
    setpoints: TagSetpoints | None = None
    alarm_class: AlarmClass | None = None
    expected_rate_s: float | None = Field(
        default=None,
        ge=0.1,
        description="Expected update period for stale detection; defaults to 30s engine-wide.",
    )

    @model_validator(mode="after")
    def _alarm_bit_has_class(self) -> "TagMeta":
        if self.signal_type is SignalType.ALARM_BIT and self.alarm_class is None:
            raise ValueError(
                "alarm_bit signal requires alarm_class"
            )
        return self


# --------------------------------------------------------------------------- #
# native_map_stub.yaml
# --------------------------------------------------------------------------- #

class NativeMapMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    native_id: str
    tag_id: str
    codec: str
    byte_order: str | None = None


class NativeMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    approved: bool = False
    mappings: list[NativeMapMapping] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Loaded pack aggregate
# --------------------------------------------------------------------------- #

class SemanticPack(BaseModel):
    """Validated, immutable view of a loaded ship-pack."""
    model_config = ConfigDict(frozen=True)

    vessel_id: str
    name: str
    imo: str | None = None
    pack_version: str
    sources: list[SourceDef]
    root: AssetNode
    tags: dict[str, TagMeta]
    native_map: NativeMap | None = None
    checksum: str
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)
