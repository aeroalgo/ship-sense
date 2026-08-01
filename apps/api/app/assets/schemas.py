from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssetNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    name: str
    status: str
    worst_tag_id: str | None = None
    children: list["AssetNode"] = []
    tag_id: str | None = None
    unit: str | None = None
    last_value: Any = None
    last_quality: str | None = None


class AssetsTreeResponse(BaseModel):
    root: AssetNode
    generated_at: datetime


AssetNode.model_rebuild()
