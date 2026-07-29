from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from emulator.tag_model import TagGenerator

from .injectors.base import BaseInjector, InjectorContext
from .injectors.value import (
    INJECTOR_TYPES,
    BadFrameInjector,
    ConnectionDropInjector,
    DuplicateInjector,
    OpcBadQualityInjector,
    TagMapChangeInjector,
    TimeJumpInjector,
    TransportInjector,
    ValueInjector,
)

__all__ = ["ScenarioRunner"]


class ScenarioRunner:
    """Apply deterministic scenario overlays around a shared tag generator."""

    good_status = "Good"
    bad_status = "BadWaitingForInitialData"

    def __init__(
        self,
        scenarios: str | Path | Mapping[str, Any],
        generator: TagGenerator,
    ) -> None:
        self.generator = generator
        self.profile = generator.profile
        self._scenario_defs = self._load(scenarios)
        self._active: list[tuple[str, int, list[BaseInjector]]] = []
        for name, definition in self._scenario_defs.items():
            if definition.get("enabled", False):
                self._activate(name, definition)

    @staticmethod
    def _load(
        source: str | Path | Mapping[str, Any],
    ) -> dict[str, Mapping[str, Any]]:
        if isinstance(source, (str, Path)):
            with Path(source).open(encoding="utf-8") as stream:
                source = yaml.safe_load(stream) or {}
        scenarios = source.get("scenarios", []) if isinstance(source, Mapping) else []
        if not isinstance(scenarios, Sequence) or isinstance(scenarios, (str, bytes)):
            raise ValueError("scenarios must be a list")
        result: dict[str, Mapping[str, Any]] = {}
        for item in scenarios:
            if not isinstance(item, Mapping) or not item.get("name"):
                raise ValueError("each scenario requires name")
            name = str(item["name"])
            if name in result:
                raise ValueError(f"duplicate scenario: {name}")
            result[name] = item
        return result

    @property
    def active_names(self) -> tuple[str, ...]:
        return tuple(name for name, _seed, _injectors in self._active)

    def _activate(self, name: str, definition: Mapping[str, Any]) -> None:
        seed = int(definition.get("seed", self.generator.seed))
        context = {"seed": seed, "tick_hz": float(self.profile.get("tick_hz", 1.0))}
        injectors: list[BaseInjector] = []
        for item in definition.get("injectors", []):
            injector_type = str(item.get("type"))
            injector_class = INJECTOR_TYPES.get(injector_type)
            if injector_class is None:
                raise ValueError(f"unsupported injector: {injector_type}")
            params = item.get("params", {})
            injectors.append(
                injector_class(
                    params=params,
                    context=InjectorContext(**context),
                )
            )
        self._active.append((name, seed, injectors))

    def enable(self, names: str | Sequence[str]) -> None:
        requested = [names] if isinstance(names, str) else list(names)
        for name in requested:
            if name not in self._scenario_defs:
                raise ValueError(f"unknown scenario: {name}")
        for name in requested:
            if name not in self.active_names:
                self._activate(name, self._scenario_defs[name])

    def disable(self, names: str | Sequence[str]) -> None:
        requested = {names} if isinstance(names, str) else set(names)
        self._active = [item for item in self._active if item[0] not in requested]

    def tick(self, t: int) -> dict[str, Any]:
        snapshot = self.generator.tick(t)
        elapsed_sec = t / float(self.profile.get("tick_hz", 1.0))
        signals = {str(signal["signal_id"]): signal for signal in self.profile["signals"]}
        for _name, _seed, injectors in self._active:
            for injector in injectors:
                if isinstance(injector, ValueInjector):
                    injector.apply(snapshot, signals, elapsed_sec)
        return snapshot

    def deliveries(self, t: int) -> list[dict[str, Any]]:
        snapshot = self.tick(t)
        elapsed_sec = t / float(self.profile.get("tick_hz", 1.0))
        deliveries = [snapshot]
        for _name, _seed, injectors in self._active:
            for injector in injectors:
                if isinstance(injector, DuplicateInjector):
                    deliveries = injector.deliveries(deliveries[0], elapsed_sec)
        return deliveries

    def get_source_timestamp(
        self,
        signal_id: str,
        default_ts: datetime,
        elapsed_sec: float,
    ) -> datetime:
        offset = sum(
            injector.offset(elapsed_sec)
            for _name, _seed, injectors in self._active
            for injector in injectors
            if isinstance(injector, TimeJumpInjector) and injector.selected(signal_id)
        )
        return default_ts + timedelta(seconds=offset)

    def get_opc_status(self, signal_id: str, elapsed_sec: float) -> str:
        for _name, _seed, injectors in self._active:
            if any(
                isinstance(injector, OpcBadQualityInjector)
                and injector.is_bad(signal_id, elapsed_sec)
                for injector in injectors
            ):
                return self.bad_status
        return self.good_status

    def filter_opc_nodes(self, nodes: list[str], elapsed_sec: float) -> list[str]:
        result = list(nodes)
        for _name, _seed, injectors in self._active:
            for injector in injectors:
                if isinstance(injector, TagMapChangeInjector):
                    result = injector.nodes(result, elapsed_sec)
        return result

    def is_connection_drop_active(self, protocol: str, elapsed_sec: float) -> bool:
        return any(
            isinstance(injector, ConnectionDropInjector) and injector.active_for(protocol, elapsed_sec)
            for _name, _seed, injectors in self._active
            for injector in injectors
        )

    def should_corrupt_modbus_frame(self, elapsed_sec: float) -> bool:
        return any(
            isinstance(injector, BadFrameInjector)
            and injector.active_for("modbus_tcp", elapsed_sec)
            for _name, _seed, injectors in self._active
            for injector in injectors
        )
