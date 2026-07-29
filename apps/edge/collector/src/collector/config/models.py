from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class PollGroup(BaseModel):
    name: str
    hz: float | None = None
    native_ids: list[str] | None = None


class PollConfig(BaseModel):
    default_hz: float = 1.0
    groups: list[PollGroup] = Field(default_factory=list)


class SubscribeConfig(BaseModel):
    publishing_interval_ms: int = 1000
    nodes_ref: str | None = None


class SecurityConfig(BaseModel):
    policy: str
    mode: str
    cert_path: str | None = None
    key_path: str | None = None


class MqttConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str
    port: int = 1883
    tls: bool = False
    client_id: str | None = None
    username: str | None = None
    password: str | None = None
    ca_cert: str | None = None
    client_cert: str | None = None
    client_key: str | None = None


class MqttSubscribeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_prefix: str
    qos: int = 1
    shared_subscription: bool = False


class MqttSourceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publish_allowed: bool = False


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    protocol: str
    endpoint: str
    poll: PollConfig | None = None
    subscribe: SubscribeConfig | None = None
    tag_map_ref: str | None = None
    readonly_profile: bool = True
    security: SecurityConfig | None = None
    extra: dict[str, Any] | None = None


class MqttSourceConfig(SourceConfig):
    model_config = ConfigDict(extra="forbid")

    protocol: Literal["mqtt"]
    connection: MqttConnectionConfig
    subscribe: MqttSubscribeConfig
    map: str
    options: MqttSourceOptions = Field(default_factory=MqttSourceOptions)


SourceConfigUnion = MqttSourceConfig | SourceConfig


def parse_source_config(value: Any) -> SourceConfigUnion:
    if isinstance(value, MqttSourceConfig | SourceConfig):
        return value
    if isinstance(value, dict) and value.get("protocol") == "mqtt":
        return MqttSourceConfig.model_validate(value)
    return SourceConfig.model_validate(value)



class TagMapEntry(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    native_id: str
    tag_id: str
    datatype: str = Field(validation_alias=AliasChoices("datatype", "type"))
    unit: str | None = None
    scale: float | None = None
    offset: float | None = None
    range_min: float | None = None
    range_max: float | None = None
    fc: int | None = None
    node_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_entry(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "native_id" not in normalized and "node_id" in normalized:
            normalized["native_id"] = normalized["node_id"]
        value_range = normalized.pop("range", None)
        if isinstance(value_range, dict):
            normalized.setdefault("range_min", value_range.get("min"))
            normalized.setdefault("range_max", value_range.get("max"))
        return normalized

    @field_validator("datatype")
    @classmethod
    def datatype_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("datatype must not be empty")
        return value


class CollectorSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: int = 1
    collector: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceConfigUnion] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_sources(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        normalized["sources"] = [
            parse_source_config(source) for source in value.get("sources", [])
        ]
        return normalized

    @model_validator(mode="after")
    def validate_mqtt_profiles(self) -> "CollectorSettings":
        return self


class CollectorSettingsLegacy(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: int = 1
    collector: dict[str, Any] = Field(default_factory=dict)
    sources: list[SourceConfig] = Field(default_factory=list)
