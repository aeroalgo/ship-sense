from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.session.roles import Role


@dataclass
class SessionState:
    session_id: UUID
    person_id: str
    name: str
    rank: str
    started_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    token: str
    default_screen: int
    roles: frozenset[Role] = frozenset()
