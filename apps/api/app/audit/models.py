from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AccessAudit:
    ts: datetime
    action: str
    person_id: str | None = None
    session_id: UUID | None = None
    source_ip: str | None = None
    details: dict[str, Any] | None = None
