from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_vessel_service
from app.vessel.schemas import VesselStateOverrideRequest, VesselStateResponse
from app.vessel.service import VesselStateService

router = APIRouter(prefix="/vessel", tags=["vessel"])


@router.get("/state", response_model=VesselStateResponse, operation_id="getVesselState")
async def get_vessel_state(
    service: Annotated[VesselStateService, Depends(get_vessel_service)],
) -> VesselStateResponse:
    return await service.state()


@router.post(
    "/state/override",
    response_model=VesselStateResponse,
    operation_id="overrideVesselState",
)
async def override_vessel_state(
    payload: VesselStateOverrideRequest,
    service: Annotated[VesselStateService, Depends(get_vessel_service)],
) -> VesselStateResponse:
    return await service.override(payload.mode, payload.ttl_minutes)
