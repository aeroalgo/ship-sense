from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.assets.schemas import AssetsTreeResponse
from app.assets.service import build_assets_tree
from app.core.dependencies import get_semantic_engine
from app.semantic.engine import SemanticEngine
from app.telemetry.service import LatestValueCache, get_latest_value_cache

router = APIRouter(tags=["assets"])


@router.get("/assets/tree", response_model=AssetsTreeResponse, operation_id="getAssetsTree")
async def get_assets_tree(
    response: Response,
    engine: SemanticEngine = Depends(get_semantic_engine),
    cache: LatestValueCache = Depends(get_latest_value_cache),
) -> AssetsTreeResponse:
    if not engine.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SEMANTIC_NOT_LOADED",
                "message": "Semantic pack is not loaded",
            },
        )
    response.headers["Cache-Control"] = "private, max-age=60"
    return AssetsTreeResponse(
        root=build_assets_tree(engine, cache),
        generated_at=datetime.now(timezone.utc),
    )
