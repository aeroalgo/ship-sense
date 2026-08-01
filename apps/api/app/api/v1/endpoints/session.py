from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.audit.models import AccessAudit
from app.audit.writer import AccessAuditWriter
from app.core.dependencies import get_db, get_session_service
from app.session.schemas import RosterResponse, SessionCreateRequest, SessionResponse
from app.session.service import SessionService, make_event
from apps.edge.storage.events_repo import EventsRepo

router = APIRouter(tags=["session"])


@router.get("/watch/roster", response_model=RosterResponse, operation_id="getWatchRoster")
async def get_roster(service: Annotated[SessionService, Depends(get_session_service)]) -> RosterResponse:
    return service.roster()


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, operation_id="createSession")
async def create_session(
    payload: SessionCreateRequest,
    response: Response,
    request: Request,
    service: Annotated[SessionService, Depends(get_session_service)],
    db=Depends(get_db),
) -> SessionResponse:
    try:
        session, previous = service.start(payload.person_id)
    except LookupError as exc:
        raise HTTPException(status_code=400, detail={"code": "PERSON_NOT_IN_ROSTER", "message": "person is not in active roster"}) from exc
    now = datetime.now(timezone.utc)
    events = EventsRepo(db)
    audit = AccessAuditWriter(db)
    if previous is not None:
        await events.insert_batch([make_event("session_ended", {"session_id": str(previous.session_id), "person_id": previous.person_id, "reason": "superseded"}, now)])
        await audit.append(AccessAudit(ts=now, person_id=previous.person_id, session_id=previous.session_id, action="logout", source_ip=request.client.host if request.client else None, details={"reason": "superseded"}))
    await events.insert_batch([make_event("session_started", {"session_id": str(session.session_id), "person_id": session.person_id, "name": session.name, "rank": session.rank, "client_ip": request.client.host if request.client else None}, now)])
    await audit.append(AccessAudit(ts=now, person_id=session.person_id, session_id=session.session_id, action="login", source_ip=request.client.host if request.client else None, details={"name": session.name, "rank": session.rank}))
    response.set_cookie("shipsense_session", session.token, httponly=True, samesite="lax", path="/")
    return session


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteSession")
async def delete_session(
    response: Response,
    shipsense_session: Annotated[str | None, Cookie()] = None,
    service: Annotated[SessionService, Depends(get_session_service)] = None,
    db=Depends(get_db),
) -> Response:
    current = service.get_current()
    if current is not None and (shipsense_session is None or shipsense_session == current.token):
        now = datetime.now(timezone.utc)
        ended = service.end()
        if ended is not None:
            await EventsRepo(db).insert_batch([make_event("session_ended", {"session_id": str(ended.session_id), "person_id": ended.person_id, "reason": "logout"}, now)])
            await AccessAuditWriter(db).append(AccessAudit(ts=now, person_id=ended.person_id, session_id=ended.session_id, action="logout", source_ip=None, details={"reason": "logout"}))
    response.delete_cookie("shipsense_session", path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
