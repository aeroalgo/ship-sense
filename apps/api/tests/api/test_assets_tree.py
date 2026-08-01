from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.dependencies import get_semantic_engine
from app.main import app
from app.telemetry.service import LatestValueCache, get_latest_value_cache
from app.semantic.engine import SemanticEngine


FIXTURE = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"


@pytest.fixture
def loaded_engine() -> SemanticEngine:
    engine = SemanticEngine(now_provider=lambda: datetime(2026, 7, 30, tzinfo=timezone.utc))
    engine.load(FIXTURE)
    engine.refresh_quarantine_from(["TAG_QUARANTINE"])
    return engine


@pytest.mark.asyncio
async def test_assets_tree_renders_hierarchy_and_worst_leaf(client, loaded_engine: SemanticEngine) -> None:
    cache = LatestValueCache()
    cache.set("TAG_GOOD", 12.5, quality="good")
    cache.set("TAG_STALE", 20.0, quality="stale")
    cache.set("TAG_QUARANTINE", 30.0, quality="quarantine")
    app.dependency_overrides[get_semantic_engine] = lambda: loaded_engine
    app.dependency_overrides[get_latest_value_cache] = lambda: cache

    try:
        response = await client.get("/api/assets/tree")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, max-age=60"
    body = response.json()
    assert body["root"]["id"] == "<vessel>"
    assert body["root"]["status"] == "quarantine"
    assert body["root"]["worst_tag_id"] == "TAG_QUARANTINE"
    leaves = [
        child
        for room in body["root"]["children"]
        for system in room["children"]
        for mechanism in system["children"]
        for child in mechanism["children"]
    ]
    assert {leaf["tag_id"] for leaf in leaves} == {
        "TAG_GOOD", "TAG_STALE", "TAG_QUARANTINE", "SKT001"
    }
    assert next(leaf for leaf in leaves if leaf["tag_id"] == "TAG_STALE")["status"] == "stale"


@pytest.mark.asyncio
async def test_assets_tree_returns_503_until_semantic_is_loaded(client) -> None:
    app.dependency_overrides[get_semantic_engine] = lambda: SemanticEngine()
    try:
        response = await client.get("/api/assets/tree")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SEMANTIC_NOT_LOADED"


@pytest.mark.asyncio
async def test_assets_tree_is_exposed_in_openapi(client) -> None:
    response = await client.get("/api/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/api/assets/tree"]["get"]
    assert operation["operationId"] == "getAssetsTree"
    assert "assets" in operation["tags"]
