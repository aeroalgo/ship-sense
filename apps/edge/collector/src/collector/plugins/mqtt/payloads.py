from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalogApsState(StrEnum):
    NORMAL = "normal"
    EXCEEDED_UNACKED = "exceeded_unacked"
    RETURNED_UNACKED = "returned_unacked"
    EXCEEDED_ACKED = "exceeded_acked"
    BLOCKED = "blocked"


class DiscreteApsState(StrEnum):
    NORMAL = "normal"
    ACTIVE_UNACKED = "active_unacked"
    PASSIVE_UNACKED = "passive_unacked"
    ACTIVE_ACKED = "active_acked"
    BLOCKED = "blocked"


class LogicalEventState(StrEnum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    BLOCKED = "blocked"


class MqttPayloadBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=False,
        strict=True,
    )

    message_type: str = Field(alias="@type")
    schema_version: str
    channel_id: str
    source_ts: datetime

    @field_validator("schema_version")
    @classmethod
    def supported_schema_version(cls, value: str) -> str:
        major = value.partition(".")[0]
        if major != "1":
            raise ValueError("unsupported_version")
        return value

    @field_validator("source_ts")
    @classmethod
    def source_timestamp_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("source_ts must be timezone-aware")
        return value.astimezone(timezone.utc)


class AnalogChannelPayload(MqttPayloadBase):
    message_type: Literal["analog"] = Field(alias="@type")
    value: float
    threshold_vvu: float
    threshold_vu: float
    threshold_nu: float
    threshold_nnu: float
    control_vvu: bool
    control_vu: bool
    control_nu: bool
    control_nnu: bool
    aps_state: AnalogApsState
    channel_test_enabled: bool = False


class DiscreteChannelPayload(MqttPayloadBase):
    message_type: Literal["discrete"] = Field(alias="@type")
    aps_state: DiscreteApsState
    input_active: bool
    channel_test_enabled: bool = False


class LogicalEventPayload(MqttPayloadBase):
    message_type: Literal["event"] = Field(alias="@type")
    event_state: LogicalEventState
    input_active: bool
    channel_test_enabled: bool = False


CylinderValues = Annotated[list[float], Field(min_length=12, max_length=12)]
CylinderPermissions = Annotated[
    list[bool], Field(min_length=12, max_length=12)
]


class ExhaustGasGroupPayload(MqttPayloadBase):
    message_type: Literal["egt"] = Field(alias="@type")
    engine_id: str
    cylinder_deviation: CylinderValues
    engine_mean_temp: float
    max_allowed_deviation: float
    operator_min_mean: float
    operator_max_mean: float
    operator_max_dev_at_min_mean: float
    operator_max_dev_at_max_mean: float
    cylinder_correction: CylinderValues
    aps_permission: CylinderPermissions


PayloadUnion = (
    AnalogChannelPayload
    | DiscreteChannelPayload
    | LogicalEventPayload
    | ExhaustGasGroupPayload
)

__all__ = [
    "AnalogApsState",
    "AnalogChannelPayload",
    "DiscreteApsState",
    "DiscreteChannelPayload",
    "ExhaustGasGroupPayload",
    "LogicalEventPayload",
    "LogicalEventState",
    "MqttPayloadBase",
    "PayloadUnion",
]
