from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.audit.writer import AccessAuditWriter
from app.core.dependencies import get_db
from app.session.authorization import Permission, require_permission

router = APIRouter(prefix="/admin/access", tags=["admin"])


@router.get("/audit", operation_id="getAdminAccessAudit")
async def get_access_audit(
    _: Annotated[object, Depends(require_permission(Permission.ACCESS_AUDIT_READ))],
    db=Depends(get_db),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    rows = await AccessAuditWriter(db).list(limit=limit, offset=offset)
    return {
        "items": [
            {
                "ts": row.ts,
                "person_id": row.person_id,
                "session_id": str(row.session_id) if row.session_id else None,
                "action": row.action,
                "source_ip": row.source_ip,
                "details": row.details or {},
            }
            for row in rows
        ],
        "limit": limit,
        "offset": offset,
    }
