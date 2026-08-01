"""Typed mnemo binding contracts loaded from ship-pack YAML."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MnemoSvg(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file: str
    viewBox: str


class MnemoDisplay(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    format: str | None = None
    unit: str | None = None


class MnemoAlarms(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    highlight_setpoint: bool = False


class MnemoElementBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    element_id: str
    svg_selector: str | None = None
    display: MnemoDisplay = Field(default_factory=MnemoDisplay)
    alarms: MnemoAlarms = Field(default_factory=MnemoAlarms)


class ValueBinding(MnemoElementBase):
    bind_type: Literal["value"]
    tag_id: str


class EnumBinding(MnemoElementBase):
    bind_type: Literal["enum"]
    tag_id: str
    enum_map: dict[str, str]
    unknown_quality: Literal["show_unknown_glyph"]


class ComputedBinding(MnemoElementBase):
    bind_type: Literal["computed"]
    compute: str


MnemoElement = Annotated[
    ValueBinding | EnumBinding | ComputedBinding,
    Field(discriminator="bind_type"),
]


class SiblingMeanDeltaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["sibling_mean_delta"]
    tags: list[str] = Field(min_length=1)

    @field_validator("tags")
    @classmethod
    def _unique_tags(cls, tags: list[str]) -> list[str]:
        if len(tags) != len(set(tags)):
            raise ValueError("computed tags must be unique")
        return tags


class MnemoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_id: str
    screen: int = Field(ge=1)
    revision: int = Field(gt=0)
    svg: MnemoSvg
    elements: list[MnemoElement] = Field(min_length=1)
    computed_bindings: dict[str, SiblingMeanDeltaSpec] = Field(default_factory=dict)

    @field_validator("elements")
    @classmethod
    def _unique_elements(cls, elements: list[MnemoElement]) -> list[MnemoElement]:
        element_ids = [element.element_id for element in elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("element_id values must be unique")
        selectors = [element.svg_selector for element in elements if element.svg_selector]
        if len(selectors) != len(set(selectors)):
            raise ValueError("svg_selector values must be unique")
        return elements

    @field_validator("elements")
    @classmethod
    def _known_computations(cls, elements: list[MnemoElement]) -> list[MnemoElement]:
        return elements
