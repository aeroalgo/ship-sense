from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml

from app.core.settings import settings
from app.events.models import Event, EventSeverity
from app.events.schemas import EventItem
from app.session.models import SessionState
from app.session.schemas import RosterPerson, RosterResponse, SessionResponse


class SessionService:
    def __init__(self, pack_path: str | Path, idle_seconds: int | None = None) -> None:
        self._path = Path(pack_path) / "roster.yaml"
        self._idle_seconds = idle_seconds if idle_seconds is not None else settings.API_SESSION_IDLE_SEC
        self._max_seconds = 12 * 60 * 60
        self._current: SessionState | None = None

    def roster(self) -> RosterResponse:
        data = self._load()
        items = [RosterPerson.model_validate(item) for item in data.get("watch", [])]
        return RosterResponse(items=sorted((item for item in items if item.active), key=lambda item: item.tile_order))

    def start(self, person_id: str, now: datetime | None = None) -> tuple[SessionResponse, SessionState | None]:
        timestamp = _utc(now or datetime.now(timezone.utc))
        person = next((item for item in self.roster().items if item.person_id == person_id), None)
        if person is None:
            raise LookupError(person_id)
        previous = self._current
        session_id = uuid4()
        state = SessionState(
            session_id=session_id,
            person_id=person.person_id,
            name=person.name,
            rank=person.rank,
            roles=person.role_set,
            started_at=timestamp,
            last_activity_at=timestamp,
            expires_at=timestamp + timedelta(seconds=self._max_seconds),
            token=str(uuid4()),
            default_screen=person.default_screen,
        )
        self._current = state
        return _response(state), previous

    def end(self, reason: str = "logout") -> SessionState | None:
        previous = self._current
        self._current = None
        return previous

    def get_current(self, now: datetime | None = None) -> SessionState | None:
        current = self._current
        if current is None:
            return None
        timestamp = _utc(now or datetime.now(timezone.utc))
        if timestamp - current.last_activity_at >= timedelta(seconds=self._idle_seconds) or timestamp >= current.expires_at:
            self._current = None
            return None
        current.last_activity_at = timestamp
        return current

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {}
        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}


def make_event(event_name: str, params: dict[str, Any], timestamp: datetime) -> Event:
    session_id = params.get("session_id", "anonymous")
    return Event(
        event_name=event_name,
        params=params,
        ts=timestamp,
        edge_ts=timestamp,
        source="api",
        severity=EventSeverity.INFO,
        idempotency_key=f"session:{session_id}:{'started' if event_name == 'session_started' else 'ended'}",
    )


def _response(state: SessionState) -> SessionResponse:
    return SessionResponse(
        session_id=str(state.session_id),
        person_id=state.person_id,
        name=state.name,
        rank=state.rank,
        started_at=state.started_at,
        expires_at=state.expires_at,
        token=state.token,
        default_screen=state.default_screen,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
