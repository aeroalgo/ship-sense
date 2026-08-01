from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class VesselMode(StrEnum):
    TRANSIT = "transit"
    ANCHORAGE = "anchorage"
    MANUAL_OVERRIDE = "manual_override"


class VesselStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: VesselMode
    override_mode: VesselMode | None = None
    rpm_ge1: float | None = None
    threshold_transit: float
    sound_enabled: bool
    night_dim: bool
    override_until: datetime | None = None


class VesselStateOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: VesselMode
    ttl_minutes: StrictInt = Field(ge=1, le=1440)
