from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

import yaml

from app.telemetry.service import LatestValue, LatestValueCache
from app.vessel.schemas import VesselMode, VesselStateResponse


class VesselConfigError(ValueError):
    pass


class LatestSignalReader(Protocol):
    def get(self, tag_id: str) -> LatestValue | None: ...


class OverrideStore(Protocol):
    async def get(self) -> tuple[VesselMode, datetime] | None: ...

    async def set(self, mode: VesselMode, expires_at: datetime) -> None: ...

    async def delete(self) -> None: ...


class VesselStateService:
    def __init__(
        self,
        pack_path: str | Path,
        reader: LatestSignalReader,
        override_store: OverrideStore,
    ) -> None:
        self._config = load_vessel_config(pack_path)
        self._reader = reader
        self._override_store = override_store

    async def state(self, *, now: datetime | None = None) -> VesselStateResponse:
        current = _utc_now(now)
        signal = self._reader.get(self._config.rpm_tag)
        rpm = _fresh_rpm(signal, current, self._config.signal_max_age_seconds)
        automatic_mode = (
            VesselMode.TRANSIT
            if rpm is not None and rpm >= self._config.transit_threshold_rpm
            else VesselMode.ANCHORAGE
        )
        override = await self._override_store.get()
        effective_mode = automatic_mode
        override_mode: VesselMode | None = None
        override_until: datetime | None = None
        if override is not None:
            target, expires_at = override
            expires_at = _as_utc(expires_at)
            if expires_at <= current:
                await self._override_store.delete()
            else:
                effective_mode = VesselMode.MANUAL_OVERRIDE
                override_mode = target
                override_until = expires_at

        policy_mode = override_mode or automatic_mode
        sound_enabled, night_dim = self._config.policies[policy_mode]
        return VesselStateResponse(
            mode=effective_mode,
            override_mode=override_mode,
            rpm_ge1=rpm,
            threshold_transit=self._config.transit_threshold_rpm,
            sound_enabled=sound_enabled,
            night_dim=night_dim,
            override_until=override_until,
        )

    async def override(
        self, mode: VesselMode, ttl_minutes: int, *, now: datetime | None = None
    ) -> VesselStateResponse:
        if mode not in (VesselMode.TRANSIT, VesselMode.ANCHORAGE):
            raise ValueError("override mode must be transit or anchorage")
        current = _utc_now(now)
        await self._override_store.set(mode, current + timedelta(minutes=ttl_minutes))
        return await self.state(now=current)


class VesselConfig:
    def __init__(
        self,
        rpm_tag: str,
        transit_threshold_rpm: float,
        signal_max_age_seconds: int,
        policies: dict[VesselMode, tuple[bool, bool]],
    ) -> None:
        self.rpm_tag = rpm_tag
        self.transit_threshold_rpm = transit_threshold_rpm
        self.signal_max_age_seconds = signal_max_age_seconds
        self.policies = policies


def load_vessel_config(pack_path: str | Path) -> VesselConfig:
    path = Path(pack_path) / "vessel.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        vessel_state = data["vessel_state"]
        rpm_tag = str(vessel_state["rpm_tag"])
        rpm_unit = str(vessel_state["rpm_unit"])
        threshold = float(vessel_state["transit_threshold_rpm"])
        max_age = int(vessel_state["signal_max_age_seconds"])
        raw_policies = vessel_state["policies"]
        policies = {
            mode: (
                bool(raw_policies[mode.value]["sound_enabled"]),
                bool(raw_policies[mode.value]["night_dim"]),
            )
            for mode in (VesselMode.TRANSIT, VesselMode.ANCHORAGE)
        }
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise VesselConfigError("invalid vessel_state configuration") from exc
    if not rpm_tag or rpm_unit != "rpm" or threshold <= 0 or max_age <= 0:
        raise VesselConfigError("invalid vessel_state configuration")
    return VesselConfig(rpm_tag, threshold, max_age, policies)


def _fresh_rpm(
    signal: LatestValue | None, now: datetime, max_age_seconds: int
) -> float | None:
    if signal is None or signal.quality in {"bad", "stale", "quarantine"}:
        return None
    if signal.timestamp is None:
        return None
    timestamp = _as_utc(signal.timestamp)
    if timestamp > now or now - timestamp > timedelta(seconds=max_age_seconds):
        return None
    try:
        value = float(signal.value)
    except (TypeError, ValueError):
        return None
    return value if value == value else None


def _utc_now(value: datetime | None) -> datetime:
    return _as_utc(value or datetime.now(timezone.utc))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
