from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MnemoSchemaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: str
    screen: int
    svg_path: str
    revision: int
    bindings_count: int


class MnemoSchemasResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[MnemoSchemaItem]


class MnemoElementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: str
    svg_selector: str | None = None
    tag_id: str | None = None
    bind_type: str
    format: str | None = None
    unit: str | None = None
    quality_overlay: bool = False
    enum_map: dict[str, str] | None = None
    unknown_quality: str | None = None
    compute: str | None = None
    params: dict[str, Any] | None = None


class MnemoSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: str
    revision: int
    viewBox: str
    elements: list[MnemoElementResponse]


class MnemoValueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: str
    tag_id: str | None = None
    value: float | int | bool | None
    status: str
    quality: str
    timestamp: datetime | None = None


class MnemoValuesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_id: str
    revision: int
    items: list[MnemoValueItem]
