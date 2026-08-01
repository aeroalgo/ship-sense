import asyncio
from datetime import datetime, timezone
from uuid import UUID

from app.reports.engine import ReportEngine
from app.reports.period import resolve_period
from app.reports.schemas import ReportRequest


UTC = timezone.utc


class Repository:
    async def next_version(self, report_id: UUID) -> int:
        return 1

    async def insert_run(self, run):
        return run


async def watermark(_request: ReportRequest) -> datetime:
    return datetime(2026, 7, 31, 23, 0, tzinfo=UTC)


def test_watch_period_can_cross_midnight() -> None:
    period = resolve_period(
        "watch_explicit",
        period_from=datetime(2026, 7, 31, 22, 0, tzinfo=UTC),
        period_to=datetime(2026, 8, 1, 6, 0, tzinfo=UTC),
    )

    assert period.from_ < period.to
    assert period.boundary_rule == "watch_explicit"


def test_preliminary_status_when_watermark_lags_period() -> None:
    request = ReportRequest(
        type="watch",
        period={
            "from": datetime(2026, 7, 31, 20, 0, tzinfo=UTC),
            "to": datetime(2026, 8, 1, 0, 0, tzinfo=UTC),
            "boundary_rule": "watch_explicit",
        },
    )

    output = asyncio.run(ReportEngine(Repository(), watermark_provider=watermark).generate(request))

    assert output.status == "preliminary"
    assert output.immutable is True
