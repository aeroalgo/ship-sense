from __future__ import annotations

import os
from pathlib import Path

from collector.config.loader import load_sources, load_tag_map, maps_dir
from collector.config.models import MqttSourceConfig, SourceConfig, TagMapEntry
from collector.domain.errors import ConfigError


def _map_path(source: SourceConfig, maps_root: Path) -> Path:
    reference = source.tag_map_ref
    if isinstance(source, MqttSourceConfig):
        reference = source.map
    elif source.protocol == "opcua" and source.subscribe is not None:
        reference = source.subscribe.nodes_ref
    if not reference:
        raise ConfigError(f"missing map reference for source {source.id}")
    return maps_root / reference.removeprefix("maps/")


def _validate_unique(entries: list[TagMapEntry], source_id: str) -> None:
    seen: set[str] = set()
    for entry in entries:
        if entry.native_id in seen:
            raise ConfigError(
                f"duplicate native_id {entry.native_id} in source {source_id}"
            )
        seen.add(entry.native_id)


def _resolve_map_entries(
    source: SourceConfig, map_path: Path
) -> list[TagMapEntry]:
    try:
        if isinstance(source, MqttSourceConfig):
            from collector.plugins.mqtt.channel_map import MqttChannelMap
            MqttChannelMap.load(map_path)
            return []
        return load_tag_map(map_path)
    except (ValueError, TypeError) as exc:
        message = f"invalid map for source {source.id}: {map_path}: {exc}"
        raise ConfigError(message) from exc


SUPPORTED_PROTOCOLS = {"modbus_tcp", "opcua", "mqtt"}


def _validate_source(
    source: SourceConfig,
    maps_root: Path,
    profile: str,
) -> None:
    if source.protocol not in SUPPORTED_PROTOCOLS:
        raise ConfigError(f"unknown protocol: {source.protocol} ({source.id})")
    if source.protocol == "modbus_tcp" and source.poll is None:
        raise ConfigError(f"missing poll config for source {source.id}")
    if source.protocol == "opcua" and source.subscribe is None:
        raise ConfigError(f"missing subscribe config for source {source.id}")
    if isinstance(source, MqttSourceConfig):
        if profile == "prod" and source.options.publish_allowed:
            raise ConfigError(
                f"publish_allowed cannot be true in prod ({source.id})"
            )
    map_path = _map_path(source, maps_root)
    if not map_path.is_file():
        raise ConfigError(f"missing map for source {source.id}: {map_path}")
    _validate_unique(_resolve_map_entries(source, map_path), source.id)


def validate_config(
    sources: list[SourceConfig] | None = None,
    maps_root: str | Path | None = None,
    profile: str | None = None,
) -> list[SourceConfig]:
    loaded_sources = sources if sources is not None else load_sources()
    root = Path(maps_root) if maps_root is not None else maps_dir()
    active_profile = profile or os.getenv("COLLECTOR_PROFILE", "dev")
    for source in loaded_sources:
        _validate_source(source, root, active_profile)
    return loaded_sources
