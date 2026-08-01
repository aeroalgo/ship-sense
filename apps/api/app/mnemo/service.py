from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.mnemo.loader import MnemoBindingLoader
from app.mnemo.models import ComputedBinding, EnumBinding, MnemoSchema, ValueBinding
from app.mnemo.schemas import (
    MnemoElementResponse,
    MnemoSchemaItem,
    MnemoSchemaResponse,
    MnemoSchemasResponse,
    MnemoValueItem,
    MnemoValuesResponse,
)
from app.telemetry.service import LatestValueCache


class MnemoService:
    def __init__(
        self,
        pack_path: str | Path,
        cache: LatestValueCache,
        *,
        schemas: Mapping[str, MnemoSchema] | None = None,
    ) -> None:
        self._pack_path = Path(pack_path)
        self._cache = cache
        self._schemas = schemas

    def _registry(self) -> Mapping[str, MnemoSchema]:
        if self._schemas is None:
            root = self._pack_path
            if not (root / "tag_map.yaml").is_file() and (root / "makarov").is_dir():
                root = root / "makarov"
            self._schemas = MnemoBindingLoader().load_all(root)
        return self._schemas

    def _pack_root(self) -> Path:
        if not (self._pack_path / "tag_map.yaml").is_file() and (self._pack_path / "makarov").is_dir():
            return self._pack_path / "makarov"
        return self._pack_path

    def list_schemas(self, *, include_generators: bool = False) -> MnemoSchemasResponse:
        schemas = self._visible_schemas(include_generators)
        return MnemoSchemasResponse(
            items=[
                MnemoSchemaItem(
                    schema_id=schema.schema_id,
                    screen=schema.screen,
                    svg_path=f"/static/{schema.svg.file}",
                    revision=schema.revision,
                    bindings_count=len(schema.elements),
                )
                for schema in sorted(schemas.values(), key=lambda item: item.schema_id)
            ]
        )

    def get_schema(self, schema_id: str, *, include_generators: bool = False) -> MnemoSchemaResponse:
        schema = self._get_visible(schema_id, include_generators)
        return MnemoSchemaResponse(
            schema_id=schema.schema_id,
            revision=schema.revision,
            viewBox=schema.svg.viewBox,
            elements=[self._element(element) for element in schema.elements],
        )

    def values(self, schema_id: str, *, include_generators: bool = False) -> MnemoValuesResponse:
        schema = self._get_visible(schema_id, include_generators)
        items: list[MnemoValueItem] = []
        for element in schema.elements:
            tag_id = getattr(element, "tag_id", None)
            if isinstance(element, ComputedBinding):
                items.append(
                    MnemoValueItem(
                        element_id=element.element_id,
                        value=None,
                        status="unknown",
                        quality="unknown",
                    )
                )
                continue
            sample = self._cache.get(tag_id) if tag_id else None
            quality = sample.quality if sample else "unknown"
            value = sample.value if sample and quality not in {"quarantine", "unknown"} else None
            items.append(
                MnemoValueItem(
                    element_id=element.element_id,
                    tag_id=tag_id,
                    value=value,
                    status="ok" if value is not None else "unknown",
                    quality=quality,
                    timestamp=sample.timestamp if sample else None,
                )
            )
        return MnemoValuesResponse(schema_id=schema.schema_id, revision=schema.revision, items=items)

    def bound_tags(self, schema_id: str, *, include_generators: bool = False) -> frozenset[str]:
        schema = self._get_visible(schema_id, include_generators)
        return frozenset(
            element.tag_id
            for element in schema.elements
            if isinstance(element, (ValueBinding, EnumBinding))
        )

    def _visible_schemas(self, include_generators: bool) -> dict[str, MnemoSchema]:
        schemas = dict(self._registry())
        if include_generators:
            return schemas
        return {schema_id: schema for schema_id, schema in schemas.items() if "generator" not in schema_id}

    def _get_visible(self, schema_id: str, include_generators: bool) -> MnemoSchema:
        schema = self._visible_schemas(include_generators).get(schema_id)
        if schema is None:
            raise LookupError(schema_id)
        return schema

    @staticmethod
    def _element(element: Any) -> MnemoElementResponse:
        display = element.display
        return MnemoElementResponse(
            element_id=element.element_id,
            svg_selector=element.svg_selector,
            tag_id=getattr(element, "tag_id", None),
            bind_type=element.bind_type,
            format=display.format,
            unit=display.unit,
            quality_overlay=element.alarms.highlight_setpoint or isinstance(element, EnumBinding),
            enum_map=element.enum_map if isinstance(element, EnumBinding) else None,
            unknown_quality=element.unknown_quality if isinstance(element, EnumBinding) else None,
            compute=element.compute if isinstance(element, ComputedBinding) else None,
            params=None,
        )
