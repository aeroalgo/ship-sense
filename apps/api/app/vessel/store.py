from __future__ import annotations

from datetime import datetime

from app.vessel.schemas import VesselMode
from app.vessel.service import OverrideStore


class InMemoryOverrideStore(OverrideStore):
    def __init__(self) -> None:
        self._record: tuple[VesselMode, datetime] | None = None

    async def get(self) -> tuple[VesselMode, datetime] | None:
        return self._record

    async def set(self, mode: VesselMode, expires_at: datetime) -> None:
        self._record = (mode, expires_at)

    async def delete(self) -> None:
        self._record = None
