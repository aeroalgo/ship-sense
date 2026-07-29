from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import BaseInjector


class ValueInjector(BaseInjector):
    def apply(self, values: dict[str, Any], signals: Mapping[str, Mapping[str, Any]], elapsed_sec: float) -> None:
        raise NotImplementedError

    def _write(self, values: dict[str, Any], signal: Mapping[str, Any], value: Any) -> None:
        for native_id in self.native_ids(signal):
            values[native_id] = value


class OutOfRangeInjector(ValueInjector):
    def apply(self, values: dict[str, Any], signals: Mapping[str, Mapping[str, Any]], elapsed_sec: float) -> None:
        if not self.is_active(elapsed_sec):
            return
        direction = str(self.params.get("direction", "high"))
        margin = float(self.params.get("margin", 1.0))
        for signal_id, signal in signals.items():
            if not self.selected(signal_id):
                continue
            value_range = signal.get("range", {})
            bound = float(value_range.get("max" if direction == "high" else "min", 0.0))
            self._write(values, signal, bound + margin if direction == "high" else bound - margin)


class StuckValueInjector(ValueInjector):
    def apply(self, values: dict[str, Any], signals: Mapping[str, Mapping[str, Any]], elapsed_sec: float) -> None:
        if not self.is_active(elapsed_sec):
            return
        stuck = getattr(self, "_stuck", {})
        for signal_id, signal in signals.items():
            if self.selected(signal_id):
                value = stuck.setdefault(
                    signal_id,
                    next((values[native] for native in self.native_ids(signal) if native in values), 0.0),
                )
                self._write(values, signal, value)
        self._stuck = stuck


class NanInfInjector(ValueInjector):
    def apply(self, values: dict[str, Any], signals: Mapping[str, Mapping[str, Any]], elapsed_sec: float) -> None:
        if not self.is_active(elapsed_sec):
            return
        value = float(self.params.get("value", "nan"))
        for signal_id, signal in signals.items():
            if self.selected(signal_id):
                self._write(values, signal, value)


class ChatterInjector(ValueInjector):
    def apply(self, values: dict[str, Any], signals: Mapping[str, Mapping[str, Any]], elapsed_sec: float) -> None:
        if not self.is_active(elapsed_sec):
            return
        frequency = float(self.params.get("frequency_hz", 10.0))
        tick = int((elapsed_sec - self.at_sec) * frequency)
        for signal_id, signal in signals.items():
            if self.selected(signal_id):
                current = next((values[native] for native in self.native_ids(signal) if native in values), False)
                self._write(values, signal, not bool(current) if tick % 2 else bool(current))


class DuplicateInjector(BaseInjector):
    def deliveries(self, snapshot: dict[str, Any], elapsed_sec: float) -> list[dict[str, Any]]:
        return [snapshot, dict(snapshot)] if self.is_active(elapsed_sec) else [snapshot]


class TransportInjector(BaseInjector):
    def active_for(self, protocol: str, elapsed_sec: float) -> bool:
        return self.is_active(elapsed_sec) and str(self.params.get("protocol", protocol)) == protocol


class ConnectionDropInjector(TransportInjector):
    pass


class BadFrameInjector(TransportInjector):
    pass


class TimeJumpInjector(BaseInjector):
    def offset(self, elapsed_sec: float) -> float:
        return float(self.params.get("offset_sec", 3600.0)) if self.is_active(elapsed_sec) else 0.0


class TagMapChangeInjector(BaseInjector):
    def nodes(self, nodes: list[str], elapsed_sec: float) -> list[str]:
        if not self.is_active(elapsed_sec):
            return nodes
        removed = {str(node) for node in self.params.get("remove", [])}
        added = [str(node) for node in self.params.get("add", [])]
        return [node for node in nodes if node not in removed] + [node for node in added if node not in nodes and node not in removed]


class OpcBadQualityInjector(BaseInjector):
    def is_bad(self, signal_id: str, elapsed_sec: float) -> bool:
        return self.is_active(elapsed_sec) and self.selected(signal_id)


INJECTOR_TYPES = {
    "signal_chatter": ChatterInjector,
    "connection_drop": ConnectionDropInjector,
    "out_of_range": OutOfRangeInjector,
    "stuck_value": StuckValueInjector,
    "time_jump": TimeJumpInjector,
    "tag_map_change": TagMapChangeInjector,
    "modbus_bad_frame": BadFrameInjector,
    "nan_inf": NanInfInjector,
    "duplicate_delivery": DuplicateInjector,
    "opc_bad_quality": OpcBadQualityInjector,
}
