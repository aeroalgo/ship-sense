from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from app.core.settings import settings
from app.mnemo.service import MnemoService
from app.mnemo.schemas import MnemoSchemaResponse, MnemoSchemasResponse, MnemoValuesResponse
from app.stream.protocol import ack_frame, hello_frame
from app.telemetry.service import LatestValueCache, get_latest_value_cache

get_mnemo_cache = get_latest_value_cache

router = APIRouter(tags=["mnemo"])


def get_mnemo_service(
    cache: LatestValueCache = Depends(get_mnemo_cache),
) -> MnemoService:
    return MnemoService(settings.SHIP_PACK_PATH, cache)


def _include_generators_allowed(include_generators: bool) -> None:
    if include_generators and not settings.API_MNEMO_INCLUDE_GENERATORS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "MNEMO_GENERATORS_DISABLED",
                "message": "Generator bindings are disabled by policy",
            },
        )


@router.get("/mnemo/schemas", response_model=MnemoSchemasResponse, operation_id="getMnemoSchemas")
async def get_mnemo_schemas(
    include_generators: Annotated[bool, Query()] = False,
    service: MnemoService = Depends(get_mnemo_service),
) -> MnemoSchemasResponse:
    _include_generators_allowed(include_generators)
    return service.list_schemas(include_generators=include_generators)


@router.get(
    "/mnemo/schemas/{schema_id}",
    response_model=MnemoSchemaResponse,
    operation_id="getMnemoSchema",
)
async def get_mnemo_schema(
    schema_id: str,
    include_generators: Annotated[bool, Query()] = False,
    service: MnemoService = Depends(get_mnemo_service),
) -> MnemoSchemaResponse:
    _include_generators_allowed(include_generators)
    try:
        return service.get_schema(schema_id, include_generators=include_generators)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MNEMO_SCHEMA_NOT_FOUND", "message": f"Unknown mnemo schema: {schema_id}"},
        ) from exc


@router.get(
    "/mnemo/schemas/{schema_id}/values",
    response_model=MnemoValuesResponse,
    operation_id="getMnemoValues",
)
async def get_mnemo_values(
    schema_id: str,
    include_generators: Annotated[bool, Query()] = False,
    service: MnemoService = Depends(get_mnemo_service),
) -> MnemoValuesResponse:
    _include_generators_allowed(include_generators)
    try:
        return service.values(schema_id, include_generators=include_generators)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MNEMO_SCHEMA_NOT_FOUND", "message": f"Unknown mnemo schema: {schema_id}"},
        ) from exc


@router.websocket("/mnemo/{schema_id}")
async def mnemo_stream(websocket: WebSocket, schema_id: str) -> None:
    bridge = websocket.app.state.stream_bridge
    service = MnemoService(settings.SHIP_PACK_PATH, get_latest_value_cache())
    try:
        bound_tags = service.bound_tags(schema_id)
    except LookupError:
        await websocket.accept()
        await websocket.send_json({"type": "error", "code": "MNEMO_SCHEMA_NOT_FOUND", "message": "Unknown mnemo schema"})
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        await websocket.send_json(hello_frame(settings.API_WS_BUFFER_SIZE))
        await bridge.connections.subscribe(websocket, {f"mnemo:{schema_id}"}, bound_tags)
        await websocket.send_json(
            ack_frame(f"mnemo:{schema_id}", [f"mnemo:{schema_id}"], {}, {})
        )
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        pass
    finally:
        await bridge.connections.disconnect(websocket)
