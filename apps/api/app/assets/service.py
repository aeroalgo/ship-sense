from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.assets.schemas import AssetNode
from app.semantic.engine import SemanticEngine
from app.semantic.models import AggregateStatus, AssetNode as SemanticAssetNode
from app.telemetry.service import LatestValueCache

_STATUS_PRIORITY = {
    "good": 0,
    "normal": 0,
    "uncertain": 1,
    "bad": 2,
    "stale": 3,
    "no_data": 4,
    "quarantine": 5,
}


def _tag_snapshot(
    tag_id: str,
    engine: SemanticEngine,
    cache: LatestValueCache,
) -> AssetNode:
    meta = engine.get_tag_meta(tag_id)
    cached = cache.get(tag_id)
    if tag_id in engine.quarantined_tags:
        status = "quarantine"
    elif cached is None:
        status = "no_data"
    else:
        status = cached.quality
    return AssetNode(
        id=f"tag:{tag_id}",
        kind="tag",
        name=meta.label or tag_id,
        status=status,
        worst_tag_id=tag_id,
        tag_id=tag_id,
        unit=meta.unit,
        last_value=cached.value if cached else None,
        last_quality=cached.quality if cached else status,
    )


def _aggregate(
    node: SemanticAssetNode,
    children: list[AssetNode],
    own_tags: list[AssetNode],
    engine: SemanticEngine,
) -> AssetNode:
    candidates = [*own_tags, *children]
    worst = max(candidates, key=lambda item: _STATUS_PRIORITY.get(item.status, 4), default=None)
    status = worst.status if worst else _status_from_engine(engine, node.id)
    return AssetNode(
        id=node.id,
        kind=node.kind.value,
        name=node.label or node.id,
        status=status,
        worst_tag_id=worst.worst_tag_id if worst else None,
        children=[*children, *own_tags],
    )


def _status_from_engine(engine: SemanticEngine, node_id: str) -> str:
    status = engine.aggregate_status(node_id)
    if status is AggregateStatus.QUARANTINE:
        return "quarantine"
    if status is AggregateStatus.NO_DATA:
        return "no_data"
    return "good"


def build_assets_tree(
    engine: SemanticEngine,
    cache: LatestValueCache,
    *,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> AssetNode:
    del now

    def visit(node: SemanticAssetNode) -> AssetNode:
        children = [visit(child) for child in node.children]
        own_tags = [_tag_snapshot(tag_id, engine, cache) for tag_id in node.tags]
        return _aggregate(node, children, own_tags, engine)

    return visit(engine.get_tree())
