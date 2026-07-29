from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


ChannelKind = Literal["analog", "discrete", "event", "egt_group"]


class MqttChannelThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expose: bool = False


class MqttChannelMapEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str
    tag_id: str
    kind: ChannelKind
    unit: str | None = None
    thresholds: MqttChannelThresholds = Field(
        default_factory=MqttChannelThresholds
    )


class MqttChannelMap:
    def __init__(self, entries: list[MqttChannelMapEntry]) -> None:
        self.entries = {entry.channel_id: entry for entry in entries}

    def lookup(self, channel_id: str) -> MqttChannelMapEntry | None:
        return self.entries.get(channel_id)

    @classmethod
    def load(cls, path: str | Path) -> MqttChannelMap:
        map_path = Path(path)
        try:
            with map_path.open(encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except OSError as exc:
            raise FileNotFoundError(
                f"MQTT channel map not found: {map_path}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(f"MQTT channel map root must be a mapping: {map_path}")
        channels = data.get("channels", [])
        if not isinstance(channels, list):
            raise ValueError(f"MQTT channel map channels must be a list: {map_path}")

        entries: list[MqttChannelMapEntry] = []
        seen: set[str] = set()
        for channel in channels:
            entry = MqttChannelMapEntry.model_validate(channel)
            if entry.channel_id in seen:
                raise ValueError(
                    f"duplicate channel_id {entry.channel_id}: {map_path}"
                )
            seen.add(entry.channel_id)
            entries.append(entry)
        return cls(entries)


__all__ = [
    "ChannelKind",
    "MqttChannelMap",
    "MqttChannelMapEntry",
    "MqttChannelThresholds",
]
