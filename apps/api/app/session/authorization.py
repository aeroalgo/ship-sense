from __future__ import annotations

from enum import StrEnum
from typing import FrozenSet

from fastapi import Cookie, Depends, HTTPException, Request, status

from app.core.dependencies import get_session_service
from app.session.models import SessionState
from app.session.roles import Role
from app.session.service import SessionService


class Permission(StrEnum):
    STORAGE_READ = "admin.storage.read"
    OTA_STATUS_READ = "admin.ota.status.read"
    ACCESS_AUDIT_READ = "admin.access_audit.read"
    OTA_APPROVE = "admin.ota.approve"
    OTA_TRIGGER = "admin.ota.trigger"


_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.WATCH_OFFICER: frozenset(),
    Role.ELECTROMECHANIC: frozenset(
        {Permission.STORAGE_READ, Permission.OTA_STATUS_READ, Permission.ACCESS_AUDIT_READ}
    ),
    Role.CHIEF_ENGINEER: frozenset(Permission),
}


def permissions_for_roles(roles: frozenset[Role]) -> frozenset[Permission]:
    permissions: set[Permission] = set()
    for role in roles:
        permissions.update(_PERMISSIONS.get(role, frozenset()))
    return frozenset(permissions)


def require_permission(permission: Permission):
    async def dependency(
        request: Request,
        shipsense_session: str | None = Cookie(default=None),
        service: SessionService = Depends(get_session_service),
    ) -> SessionState:
        current = service.get_current()
        if current is None or shipsense_session != current.token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "SESSION_REQUIRED", "message": "active session is required"},
            )
        if permission not in permissions_for_roles(current.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "permission denied"},
            )
        request.state.admin_permission = permission.value
        return current

    return dependency
