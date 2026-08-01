from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.audit.models import AccessAudit
from app.audit.writer import AccessAuditWriter
from app.core.dependencies import get_db, get_vessel_service
from app.session.authorization import Permission, require_permission
from app.session.models import SessionState
from app.vessel.schemas import VesselMode
from app.vessel.service import VesselStateService
from apps.edge.ota.gate import can_update


class OtaCoordinator(Protocol):
    async def status(self) -> dict[str, object]: ...

    async def approve(self) -> dict[str, object]: ...

    async def trigger(self) -> dict[str, object]: ...


class InMemoryOtaCoordinator:
    def __init__(self, vessel: VesselStateService) -> None:
        self._vessel = vessel
        self._approved = False

    async def status(self) -> dict[str, object]:
        vessel_state = await self._vessel.state()
        update_allowed = can_update(anchored=vessel_state.mode == VesselMode.ANCHORAGE) == "allowed"
        return {
            "active_slot": None,
            "pending_slot": None,
            "download_pct": None,
            "last_error": None,
            "vessel_state": vessel_state.mode.value,
            "update_allowed": update_allowed,
            "approved": self._approved,
        }

    async def approve(self) -> dict[str, object]:
        result = await self.status()
        if not result["update_allowed"]:
            raise PermissionError("OTA update requires anchorage")
        self._approved = True
        return await self.status()

    async def trigger(self) -> dict[str, object]:
        result = await self.status()
        if not result["update_allowed"]:
            raise PermissionError("OTA update requires anchorage")
        if not self._approved:
            raise PermissionError("OTA approval is required")
        return {**result, "status": "triggered"}


_coordinator: InMemoryOtaCoordinator | None = None


def get_ota_coordinator(
    vessel: Annotated[VesselStateService, Depends(get_vessel_service)],
) -> InMemoryOtaCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = InMemoryOtaCoordinator(vessel)
    return _coordinator


router = APIRouter(prefix="/admin/ota", tags=["admin"], dependencies=[])


@router.get("/status", operation_id="getAdminOtaStatus")
async def get_status(
    _: Annotated[object, Depends(require_permission(Permission.OTA_STATUS_READ))],
    coordinator: Annotated[OtaCoordinator, Depends(get_ota_coordinator)],
) -> dict[str, object]:
    return await coordinator.status()


@router.post("/approve", operation_id="approveAdminOta")
async def approve(
    request: Request,
    current: Annotated[SessionState, Depends(require_permission(Permission.OTA_APPROVE))],
    coordinator: Annotated[OtaCoordinator, Depends(get_ota_coordinator)],
    db=Depends(get_db),
) -> dict[str, object]:
    try:
        result = await coordinator.approve()
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "OTA_NOT_ALLOWED", "message": str(exc)}) from exc
    await _audit_ota_action(request, current, db, "ota_approve")
    return result


@router.post("/trigger", operation_id="triggerAdminOta")
async def trigger(
    request: Request,
    current: Annotated[SessionState, Depends(require_permission(Permission.OTA_TRIGGER))],
    coordinator: Annotated[OtaCoordinator, Depends(get_ota_coordinator)],
    db=Depends(get_db),
) -> dict[str, object]:
    try:
        result = await coordinator.trigger()
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "OTA_NOT_ALLOWED", "message": str(exc)}) from exc
    await _audit_ota_action(request, current, db, "ota_trigger")
    return result


async def _audit_ota_action(request: Request, current: SessionState, db, action: str) -> None:
    await AccessAuditWriter(db).append(
        AccessAudit(
            ts=datetime.now(timezone.utc),
            person_id=current.person_id,
            session_id=current.session_id,
            action=action,
            source_ip=request.client.host if request.client else None,
            details={"permission": request.state.admin_permission},
        )
    )
