from fastapi import APIRouter, Depends

from app.core.dependencies import get_session_service
from app.reports.service import ReportsService
from app.session.service import SessionService

router = APIRouter(tags=["reports"])


@router.get("/watch/schedule", operation_id="getWatchSchedule")
async def get_watch_schedule(
    session_service: SessionService = Depends(get_session_service),
) -> dict[str, object]:
    return ReportsService.schedule(session_service)
