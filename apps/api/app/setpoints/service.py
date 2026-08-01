from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.setpoints.schemas import (
    Segment,
    SetpointChangelogItem,
    SetpointChangelogResponse,
    SetpointHistoryResponse,
    SetpointItem,
    SetpointsListResponse,
)


class SetpointsService:
    def __init__(self, pack_path: str | Path) -> None:
        self._path = Path(pack_path) / "setpoints.yaml"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {}
        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}

    def list_all(self) -> SetpointsListResponse:
        data = self._load()
        items = [
            SetpointItem(
                tag_id=str(item["tag_id"]),
                value=float(item["value"]),
                unit=str(item["unit"]),
                label=str(item["label"]),
                effective_from=_parse_timestamp(item["effective_from"]),
            )
            for item in data.get("items", [])
        ]
        return SetpointsListResponse(items=items)

    def history(self, tag: str) -> SetpointHistoryResponse:
        data = self._load()
        for item in data.get("items", []):
            if item.get("tag_id") == tag:
                segments = [
                    Segment(
                        from_ts=_parse_timestamp(segment["from_ts"]),
                        to_ts=(
                            _parse_timestamp(segment["to_ts"])
                            if segment.get("to_ts") is not None
                            else None
                        ),
                        value=float(segment["value"]),
                    )
                    for segment in item.get("history", [])
                ]
                return SetpointHistoryResponse(tag_id=tag, segments=segments)
        raise LookupError(tag)

    @staticmethod
    def changelog_rows(rows: list[Any]) -> SetpointChangelogResponse:
        items = []
        for row in rows:
            params = dict(row.params or {})
            try:
                items.append(
                    SetpointChangelogItem(
                        id=str(row.event_id),
                        ts=_utc(row.official_ts),
                        tag_id=str(params["tag_id"]),
                        old_value=float(params["old_value"]),
                        new_value=float(params["new_value"]),
                        unit=str(params["unit"]),
                        source=str(row.source),
                        actor=str(params["actor"]) if params.get("actor") is not None else None,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        items.sort(key=lambda item: (item.ts, item.id))
        return SetpointChangelogResponse(items=items)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    else:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return _utc(timestamp)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
