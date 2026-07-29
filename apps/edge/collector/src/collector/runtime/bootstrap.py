from __future__ import annotations

import os
from pathlib import Path
from collector.config.loader import load_settings, load_tag_map
from collector.config.models import MqttSourceConfig, SourceConfig, TagMapEntry
from collector.plugins.mqtt.channel_map import MqttChannelMap
from collector.core.event_detector import EventDetector
from collector.core.normalizer import Normalizer
from collector.core.restart_policy import RestartPolicy
from collector.core.supervisor import SourceSupervisor
from collector.domain.errors import ConfigError
from collector.domain.interfaces import SourceConnector
from collector.health.aggregator import HealthAggregator
from collector.plugins.registry import PluginRegistry
from collector.sink.ipc_sink import IpcCanonicalSink
from collector.sink.null_sink import NullSink
from collector.runtime.endpoints import (
    parse_modbus_endpoint,
    parse_writer_endpoint,
)


def filter_sources(
    sources: list[SourceConfig], source_filter: str | None,
) -> list[SourceConfig]:
    if not source_filter:
        return sources
    selected = {item.strip() for item in source_filter.split(",") if item.strip()}
    return [source for source in sources if source.id in selected]


def _register_builtins(maps_dir: Path) -> None:
    from collector.plugins.modbus.connector import ModbusTcpConnector
    from collector.plugins.mqtt.connector import MqttConnector
    from collector.plugins.opcua.connector import OpcUaConnector

    def modbus_factory(config: SourceConfig) -> SourceConnector:
        if not config.tag_map_ref:
            raise ConfigError(f"source {config.id} has no tag_map_ref")
        tag_map = load_tag_map(maps_dir / config.tag_map_ref)
        host, port = parse_modbus_endpoint(config.endpoint)
        from collector.plugins.modbus.client import AsyncModbusClient

        return ModbusTcpConnector(
            config,
            AsyncModbusClient(host=host, port=port),
            tag_map,
        )

    def opcua_factory(config: SourceConfig) -> SourceConnector:
        ref = _map_ref(config)
        if ref is None:
            raise ConfigError(f"source {config.id} has no OPC UA node map")
        tag_map = load_tag_map(maps_dir / ref)
        return OpcUaConnector(config, tag_map=tag_map)

    def mqtt_factory(config: SourceConfig) -> SourceConnector:
        if not isinstance(config, MqttSourceConfig):
            config = MqttSourceConfig.model_validate(config.model_dump())
        ref = _map_ref(config)
        if ref is None:
            raise ConfigError(f"source {config.id} has no MQTT channel map")
        map_path = Path(ref)
        if not map_path.is_absolute():
            map_path = maps_dir.parent / map_path
        return MqttConnector(
            config,
            channel_map=MqttChannelMap.load(map_path),
        )

    PluginRegistry.register("modbus_tcp", modbus_factory)
    PluginRegistry.register("mqtt", mqtt_factory)
    PluginRegistry.register("opcua", opcua_factory)


def _map_ref(config: SourceConfig) -> str | None:
    if isinstance(config, MqttSourceConfig):
        return config.map
    return config.tag_map_ref or (
        config.subscribe.nodes_ref if config.subscribe else None
    )


def _resolve_map_path(config: SourceConfig, maps_dir: Path) -> Path:
    reference = _map_ref(config)
    if reference is None:
        raise ConfigError(f"source {config.id} has no tag map")
    path = Path(reference)
    if not path.is_absolute():
        if reference.startswith("maps/"):
            path = maps_dir.parent / path
        else:
            path = maps_dir / path
    return path


def _mqtt_tag_entries(channel_map: MqttChannelMap) -> list[TagMapEntry]:
    return [
        TagMapEntry(
            native_id=entry.channel_id,
            tag_id=entry.tag_id,
            datatype=entry.kind,
            unit=entry.unit,
        )
        for entry in channel_map.entries.values()
    ]


def _load_source_entries(
    config: SourceConfig, maps_dir: Path
) -> list[TagMapEntry]:
    map_path = _resolve_map_path(config, maps_dir)
    if isinstance(config, MqttSourceConfig):
        return _mqtt_tag_entries(MqttChannelMap.load(map_path))
    return load_tag_map(map_path)


def build_normalizer(
    tag_map: dict[str, TagMapEntry], config_root: Path,
) -> Normalizer:
    return Normalizer.from_yaml(
        tag_map=tag_map,
        quality_rules_path=config_root / "quality_rules.yaml",
        units_path=config_root / "units.yaml",
        event_detector=EventDetector(),
    )


def build_sink(endpoint: str | None):
    if endpoint:
        return IpcCanonicalSink(parse_writer_endpoint(endpoint))
    return NullSink()


def build_runtime(
    *,
    sources_path: Path,
    maps_dir: Path,
    snapshot_path: Path | None,
    writer_endpoint: str | None,
    source_filter: str | None,
):
    settings = load_settings(sources_path)
    selected = filter_sources(settings.sources, source_filter)
    if not selected:
        raise ConfigError("no collector sources selected")
    _register_builtins(maps_dir)

    import asyncio

    raw_queue = asyncio.Queue(
        maxsize=int(settings.collector.get("raw_queue_maxsize", 10000))
    )
    health = HealthAggregator()
    tag_map: dict[str, TagMapEntry] = {}
    connectors: list[SourceConnector] = []
    supervisors: list[SourceSupervisor] = []
    for config in selected:
        entries = _load_source_entries(config, maps_dir)
        for entry in entries:
            previous = tag_map.get(entry.native_id)
            if previous is not None and previous != entry:
                raise ConfigError(f"duplicate native_id across sources: {entry.native_id}")
            tag_map[entry.native_id] = entry
        connector = PluginRegistry.create(config)
        connectors.append(connector)
        supervisors.append(
            SourceSupervisor(
                connector,
                raw_queue,
                RestartPolicy(),
                [entry.native_id for entry in entries],
            )
        )

    from collector.app import build_collector_app

    normalizer = build_normalizer(tag_map, maps_dir.parent)
    app = build_collector_app(
        raw_queue=raw_queue,
        sink=build_sink(writer_endpoint),
        sources=connectors,
        supervisors=supervisors,
        health=health,
        snapshot_path=snapshot_path,
        normalize=normalizer,
    )
    return app


def runtime_from_environment(
    *,
    snapshot_path: Path | None,
    sources_path: Path | None = None,
    maps_dir: Path | None = None,
    writer_endpoint: str | None = None,
    source_filter: str | None = None,
):
    root = Path(__file__).resolve().parents[3]
    return build_runtime(
        sources_path=sources_path
        or Path(
            os.getenv(
                "COLLECTOR_SOURCES_PATH",
                root / "config" / "sources.dev.yaml",
            )
        ),
        maps_dir=maps_dir
        or Path(os.getenv("COLLECTOR_MAPS_DIR", root / "maps")),
        snapshot_path=snapshot_path,
        writer_endpoint=writer_endpoint or os.getenv("SHIPSSENSE_WRITER_ENDPOINT"),
        source_filter=source_filter or os.getenv("SHIPSSENSE_SMOKE_SOURCES"),
    )
