from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from emulator.physics.daily_patterns import daily_factor


GeneratorProfile = dict[str, Any]


def load_profile(path: str | Path) -> GeneratorProfile:
    """Load and validate a profile without parsing YAML during a tick."""
    with Path(path).open(encoding="utf-8") as stream:
        profile = yaml.safe_load(stream)
    if isinstance(profile, dict) and isinstance(profile.get("profile"), dict):
        profile = {**profile["profile"], "signals": profile.get("signals", [])}
    if not isinstance(profile, dict) or not isinstance(profile.get("signals"), list):
        raise ValueError("profile must contain a signals list")
    signals = profile["signals"]
    if len({signal.get("signal_id") for signal in signals}) != len(signals):
        raise ValueError("signal_id values must be unique")
    signal_ids = {signal.get("signal_id") for signal in signals}
    for signal in signals:
        if not isinstance(signal, dict) or not signal.get("signal_id"):
            raise ValueError("each signal requires signal_id")
        native_ids = signal.get("native_ids")
        if not isinstance(native_ids, dict) or not native_ids:
            raise ValueError(f"signal {signal['signal_id']} requires native_ids")
        generator = signal.get("generator", {})
        if generator.get("kind") == "correlated":
            drivers = generator.get("drivers", [])
            unknown = set(drivers) - signal_ids
            if unknown:
                raise ValueError(f"signal {signal['signal_id']} has unknown drivers: {sorted(unknown)}")
    return profile


def _stable_noise(seed: int, profile_id: str, signal_id: str, tick: int, stream: str) -> float:
    key = f"{seed}:{profile_id}:{signal_id}:{tick}:{stream}".encode()
    digest = hashlib.blake2b(key, digest_size=8).digest()
    return random.Random(int.from_bytes(digest, "big")).uniform(-1.0, 1.0)


def _signal_range(signal: Mapping[str, Any]) -> tuple[float, float] | None:
    value_range = signal.get("range")
    if not isinstance(value_range, Mapping):
        return None
    lower, upper = value_range.get("min"), value_range.get("max")
    if isinstance(lower, (int, float)) and isinstance(upper, (int, float)):
        return float(lower), float(upper)
    return None


def _bounded(value: Any, value_range: tuple[float, float] | None) -> Any:
    if value_range is None or not isinstance(value, (int, float)) or isinstance(value, bool):
        return value
    return min(value_range[1], max(value_range[0], value))


class TagGenerator:
    """Deterministic profile-driven generator returning one complete snapshot per tick."""

    def __init__(self, seed: int, profile: GeneratorProfile):
        self.seed = seed
        self.profile = profile
        self.profile_id = str(profile.get("id", "profile"))
        signals_by_id = {str(signal["signal_id"]): signal for signal in profile["signals"]}
        self._signals = self._topological_signals(signals_by_id)
        self._previous: dict[str, float] = {}
        self._validate_graph()

    @staticmethod
    def _topological_signals(signals_by_id: dict[str, Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        ordered: list[Mapping[str, Any]] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(signal_id: str) -> None:
            if signal_id in visiting:
                raise ValueError("generator dependency graph contains a cycle")
            if signal_id in visited:
                return
            visiting.add(signal_id)
            for dependency in signals_by_id[signal_id].get("generator", {}).get("drivers", []):
                if dependency not in signals_by_id:
                    raise ValueError(f"unknown driver: {dependency}")
                visit(dependency)
            visiting.remove(signal_id)
            visited.add(signal_id)
            ordered.append(signals_by_id[signal_id])

        for signal_id in sorted(signals_by_id):
            visit(signal_id)
        return ordered

    def _validate_graph(self) -> None:
        dependencies = {
            str(signal["signal_id"]): list(signal.get("generator", {}).get("drivers", []))
            for signal in self._signals
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(signal_id: str) -> None:
            if signal_id in visiting:
                raise ValueError("generator dependency graph contains a cycle")
            if signal_id in visited:
                return
            visiting.add(signal_id)
            for dependency in dependencies[signal_id]:
                if dependency not in dependencies:
                    raise ValueError(f"unknown driver: {dependency}")
                visit(dependency)
            visiting.remove(signal_id)
            visited.add(signal_id)

        for signal_id in dependencies:
            visit(signal_id)

    def tick(self, t: int) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for signal in self._signals:
            signal_id = str(signal["signal_id"])
            generator = signal.get("generator", {})
            kind = generator.get("kind", "constant")
            noise_sample = _stable_noise(self.seed, self.profile_id, signal_id, t, "value")
            if kind == "constant":
                value = generator.get("value", generator.get("baseline", 0.0))
            elif kind == "random_walk":
                previous = self._previous.get(signal_id, float(generator.get("baseline", 0.0)))
                value = previous + float(generator.get("step", generator.get("noise", 1.0))) * noise_sample
                self._previous[signal_id] = value
            elif kind == "periodic":
                value = float(generator.get("baseline", 0.0)) + float(generator.get("amplitude", 1.0)) * daily_factor(
                    t / float(self.profile.get("tick_hz", 1.0)),
                    period=float(generator.get("period", 86400.0)),
                    amplitude=1.0,
                    phase=float(generator.get("phase", 0.0)),
                )
            elif kind == "discrete":
                choices = list(generator.get("values", [False, True]))
                index = int(abs(noise_sample) * len(choices)) % len(choices)
                value = choices[index]
            elif kind == "correlated":
                drivers = {name: float(values[name]) for name in generator.get("drivers", [])}
                coefficients = generator.get("coefficients")
                if coefficients is None:
                    coefficients = [generator.get("coeff", 0.0)] * len(drivers)
                value = float(generator.get("baseline", 0.0)) + sum(
                    drivers[name] * float(coefficient) for name, coefficient in zip(drivers, coefficients, strict=True)
                )
                value += float(generator.get("noise", 0.0)) * noise_sample
            else:
                raise ValueError(f"unsupported generator kind: {kind}")
            values[signal_id] = _bounded(value, _signal_range(signal))
        return {
            str(native_id): values[str(signal["signal_id"])]
            for signal in self._signals
            for native_id in signal["native_ids"].values()
        }
