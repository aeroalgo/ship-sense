from __future__ import annotations

from datetime import datetime

from apps.edge.storage.events_repo import EventFilters, EventsRepo


async def fetch_setpoint_changes(
    session,
    *,
    from_ts: datetime | None,
    to_ts: datetime | None,
    limit: int,
):
    return await EventsRepo(session).query_journal(
        EventFilters(ts_from=from_ts, ts_to=to_ts, event_name="setpoint_changed"),
        limit=limit,
    )
