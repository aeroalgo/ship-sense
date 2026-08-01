from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.reports.schemas import BoundaryRule, ReportPeriod


def resolve_period(
    boundary_rule: BoundaryRule,
    *,
    period_from: datetime | None = None,
    period_to: datetime | None = None,
    reference: datetime | None = None,
) -> ReportPeriod:
    """Resolve a report interval without silently filling missing data."""
    if boundary_rule in {"watch_explicit", "custom"}:
        if period_from is None or period_to is None:
            raise ValueError("period_from and period_to are required for explicit periods")
        resolved_from, resolved_to = period_from, period_to
    elif boundary_rule == "calendar_utc":
        anchor = reference or period_from or datetime.now(timezone.utc)
        resolved_from = anchor.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        resolved_to = resolved_from + timedelta(days=1)
    else:
        anchor = reference or period_to or period_from
        if anchor is None:
            raise ValueError("reference is required for vessel_day_noon")
        anchor = anchor.astimezone(timezone.utc)
        noon = anchor.replace(hour=12, minute=0, second=0, microsecond=0)
        resolved_to = noon if anchor >= noon else noon - timedelta(days=1)
        resolved_from = resolved_to - timedelta(days=1)

    if resolved_from.tzinfo is None or resolved_to.tzinfo is None:
        raise ValueError("report period timestamps must include timezone")
    if resolved_from >= resolved_to:
        raise ValueError("report period must have from before to")
    return ReportPeriod(from_=resolved_from, to=resolved_to, boundary_rule=boundary_rule)
