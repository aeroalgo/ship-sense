from fastapi import APIRouter, Depends, Request, Response, status

from app.core.dependencies import get_db
from app.core.settings import settings
from app.health.schemas import HealthResponse, SourcesStatusResponse
from app.health.service import HealthService

router = APIRouter(tags=["health"])
_service = HealthService(snapshot_path=settings.API_COLLECTOR_HEALTH_PATH)


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def health(
    response: Response,
    request: Request,
    session=Depends(get_db),
) -> HealthResponse:
    bridge = getattr(request.app.state, "stream_bridge", None)
    connections = len(getattr(getattr(bridge, "connections", None), "_connections", {}))
    result = await _service.build_health(session, ws_connections=connections)
    if result.status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get(
    "/sources/status",
    response_model=SourcesStatusResponse,
    operation_id="getSourcesStatus",
)
def sources_status() -> SourcesStatusResponse:
    return _service.sources_status()
