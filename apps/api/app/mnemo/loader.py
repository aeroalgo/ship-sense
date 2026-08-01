"""Fail-closed loader for immutable mnemo schema snapshots."""
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml
from pydantic import ValidationError

from app.mnemo.models import ComputedBinding, EnumBinding, MnemoSchema


class MnemoConfigError(ValueError):
    """A mnemo YAML file cannot be published into the registry."""


class MnemoBindingLoader:
    def load_all(self, ship_pack_root: Path | str) -> MappingProxyType[str, MnemoSchema]:
        root = Path(ship_pack_root)
        tag_map = self._load_tags(root / "tag_map.yaml")
        binding_dir = root / "mnemo_bindings"
        if not binding_dir.is_dir():
            raise MnemoConfigError(f"missing directory: {binding_dir}")

        schemas: dict[str, MnemoSchema] = {}
        for path in sorted(binding_dir.glob("*.yaml")):
            schema = self._load_file(path)
            expected_id = path.stem
            if schema.schema_id != expected_id:
                raise MnemoConfigError(
                    f"{path.name}: filename/schema_id mismatch ({expected_id} != {schema.schema_id})"
                )
            if schema.schema_id in schemas:
                raise MnemoConfigError(f"{path.name}: duplicate schema_id {schema.schema_id}")
            self._validate_references(schema, tag_map, path)
            schemas[schema.schema_id] = schema
        return MappingProxyType(schemas)

    @staticmethod
    def _load_tags(path: Path) -> set[str]:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            tags = payload["tags"]
            if not isinstance(tags, dict):
                raise TypeError("tags must be a mapping")
            return set(tags)
        except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
            raise MnemoConfigError(f"{path.name}: invalid tag map: {exc}") from exc

    @staticmethod
    def _load_file(path: Path) -> MnemoSchema:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            return MnemoSchema.model_validate(payload)
        except (OSError, yaml.YAMLError, ValidationError, TypeError) as exc:
            raise MnemoConfigError(f"{path.name}: invalid mnemo schema: {exc}") from exc

    @staticmethod
    def _validate_references(schema: MnemoSchema, tags: set[str], path: Path) -> None:
        for element in schema.elements:
            if isinstance(element, (EnumBinding, ComputedBinding)) and isinstance(element, EnumBinding):
                pass
            tag_id = getattr(element, "tag_id", None)
            if tag_id and tag_id not in tags:
                raise MnemoConfigError(f"{path.name}: unknown tag_id {tag_id}")
            if isinstance(element, ComputedBinding) and element.compute not in schema.computed_bindings:
                raise MnemoConfigError(f"{path.name}: unknown computed spec {element.compute}")
        for name, spec in schema.computed_bindings.items():
            unknown = sorted(set(spec.tags) - tags)
            if unknown:
                raise MnemoConfigError(f"{path.name}: computed {name} has unknown tags {unknown}")


def load_all(ship_pack_root: Path | str) -> MappingProxyType[str, MnemoSchema]:
    return MnemoBindingLoader().load_all(ship_pack_root)
