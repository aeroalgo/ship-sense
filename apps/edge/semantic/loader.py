"""Ship-pack loader (s12).

Reads YAML files from a pack directory, validates cross-references and
uniqueness constraints (plan §794–802), builds the in-memory asset tree and
returns a frozen :class:`SemanticPack` with a deterministic sha256 checksum.

Fail-fast: every structural problem raises :class:`SemanticPackError` carrying
the offending file name, an optional YAML line number and a human message
(plan §216).
"""
from __future__ import annotations

import hashlib
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from apps.edge.semantic.models import (
    AssetNode,
    AssetNodeKind,
    EngineRoomNode,
    MechanismNode,
    NativeMap,
    SemanticPack,
    SourceDef,
    SystemNode,
    TagMeta,
    VesselDef,
)

log = logging.getLogger(__name__)

REQUIRED_FILES = (
    "vessel.yaml",
    "assets.yaml",
    "tag_map.yaml",
)
OPTIONAL_FILES = ("native_map_stub.yaml", "timezone.yaml")
# tolerance for tag_count_expected mismatch (plan §801 — 0 for production packs)
COUNT_TOLERANCE = 0


class SemanticPackError(Exception):
    """Raised on any structural ship-pack problem."""

    def __init__(
        self,
        message: str,
        *,
        file: str | None = None,
        line: int | None = None,
    ) -> None:
        self.file = file
        self.line = line
        loc = f"{file or '<pack>'}"
        if line is not None:
            loc += f":{line}"
        super().__init__(f"{loc}: {message}")


# --------------------------------------------------------------------------- #
# Low-level YAML read
# --------------------------------------------------------------------------- #

class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that raises on duplicate mapping keys."""


def _unique_key_constructor(loader: yaml.Loader, node: yaml.MappingNode,
                            deep: bool = False) -> dict:
    seen: set[str] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise SemanticPackError(
                f"duplicate key '{key}'",
                file=None,
                line=key_node.start_mark.line + 1,
            )
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_key_constructor,
)


def _read_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        loaded = yaml.load(text, Loader=_UniqueKeyLoader)
    except SemanticPackError as exc:
        # re-raise with file context
        raise SemanticPackError(
            str(exc).split(": ", 1)[-1], file=path.name, line=exc.line
        ) from None
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 1 if mark else None
        raise SemanticPackError(
            f"YAML parse error: {exc}", file=path.name, line=line
        ) from None
    if not isinstance(loaded, dict):
        raise SemanticPackError(
            f"expected a YAML mapping at top level, got {type(loaded).__name__}",
            file=path.name,
        )
    return loaded


def _file_mark(raw: Any, key: str | None = None) -> int | None:
    """Try to recover a YAML line for ``key`` from a ruamel/pyyaml node."""
    node = raw if key is None else (raw.get(key) if isinstance(raw, dict) else None)
    mark = getattr(node, "start_mark", None) or getattr(node, "_start_mark", None)
    return mark.line + 1 if mark else None


# --------------------------------------------------------------------------- #
# Per-file loaders
# --------------------------------------------------------------------------- #

def _load_vessel(raw: dict[str, Any]) -> tuple[VesselDef, list[SourceDef]]:
    vessel_raw = raw.get("vessel")
    if vessel_raw is None:
        raise SemanticPackError("missing 'vessel' mapping", file="vessel.yaml")
    sources_raw = raw.get("sources", [])
    try:
        vessel = VesselDef.model_validate(vessel_raw)
        sources = [SourceDef.model_validate(s) for s in sources_raw]
    except ValidationError as exc:
        _raise_pydantic(exc, "vessel.yaml")
    if not sources:
        raise SemanticPackError("'sources' is empty", file="vessel.yaml")
    return vessel, sources


def _build_tree(
    engine_rooms_raw: list[dict[str, Any]],
) -> AssetNode:
    if not engine_rooms_raw:
        raise SemanticPackError("'engine_rooms' is empty", file="assets.yaml")
    try:
        rooms = [EngineRoomNode.model_validate(er) for er in engine_rooms_raw]
    except ValidationError as exc:
        _raise_pydantic(exc, "assets.yaml")

    children: list[AssetNode] = []
    for room in rooms:
        room_node = AssetNode(
            kind=AssetNodeKind.ENGINE_ROOM, id=room.id, label=room.label
        )
        for system in room.systems:
            sys_node = AssetNode(
                kind=AssetNodeKind.SYSTEM, id=system.id, label=system.label
            )
            for mech in system.mechanisms:
                mech_node = AssetNode(
                    kind=AssetNodeKind.MECHANISM,
                    id=mech.id,
                    label=mech.label,
                    tags=list(mech.tags),
                )
                sys_node.children.append(mech_node)
            room_node.children.append(sys_node)
        children.append(room_node)

    return AssetNode(
        kind=AssetNodeKind.VESSEL,
        id="<vessel>",
        children=children,
    )


def _mechanisms(root: AssetNode):
    """Yield (mechanism node) for every mechanism in the tree."""
    for room in root.children:
        for system in room.children:
            for mech in system.children:
                yield mech


def _load_tag_map(raw: dict[str, Any]) -> dict[str, TagMeta]:
    tags_raw = raw.get("tags")
    if tags_raw is None:
        raise SemanticPackError("missing 'tags' mapping", file="tag_map.yaml")
    if not isinstance(tags_raw, dict):
        raise SemanticPackError(
            f"'tags' must be a mapping, got {type(tags_raw).__name__}",
            file="tag_map.yaml",
        )
    tags: dict[str, TagMeta] = {}
    for tag_id, body in tags_raw.items():
        if not isinstance(body, dict):
            raise SemanticPackError(
                f"tag '{tag_id}' body must be a mapping",
                file="tag_map.yaml",
            )
        if tag_id in tags:
            raise SemanticPackError(
                f"duplicate tag '{tag_id}'",
                file="tag_map.yaml",
                line=_file_mark(tags_raw, tag_id),
            )
        try:
            tags[tag_id] = TagMeta.model_validate({**body, **{"_id": tag_id}})
        except ValidationError:
            try:
                tags[tag_id] = TagMeta.model_validate(body)
            except ValidationError as exc:
                _raise_pydantic(exc, "tag_map.yaml", hint=f"tag '{tag_id}'")
    return tags


def _load_native_map(raw: dict[str, Any]) -> NativeMap:
    try:
        return NativeMap.model_validate(raw)
    except ValidationError as exc:
        _raise_pydantic(exc, "native_map_stub.yaml")


# --------------------------------------------------------------------------- #
# Cross-file validation
# --------------------------------------------------------------------------- #

def _validate_uniqueness(root: AssetNode) -> None:
    seen: dict[str, int] = {}
    for mech in _mechanisms(root):
        for tag in mech.tags:
            if tag in seen:
                raise SemanticPackError(
                    f"duplicate tag '{tag}' across mechanisms "
                    f"(first at mechanism, second in '{mech.id}')",
                    file="assets.yaml",
                )
            seen[tag] = 1


def _validate_tag_refs(
    tags: dict[str, TagMeta],
    root: AssetNode,
    sources: list[SourceDef],
) -> None:
    asset_tags = set()
    for mech in _mechanisms(root):
        asset_tags.update(mech.tags)

    source_ids = {s.id for s in sources}

    # tag in tag_map but not in assets -> orphan
    for tag_id in tags:
        if tag_id not in asset_tags:
            raise SemanticPackError(
                f"tag '{tag_id}' declared in tag_map.yaml but absent from assets tree"
            )

    # tag in assets but not in tag_map -> missing meta
    for tag_id in asset_tags:
        if tag_id not in tags:
            raise SemanticPackError(
                f"tag '{tag_id}' present in assets but missing from tag_map.yaml",
                file="assets.yaml",
            )

    # source_id resolution
    for tag_id, meta in tags.items():
        if meta.source_id not in source_ids:
            raise SemanticPackError(
                f"tag '{tag_id}' references unknown source_id '{meta.source_id}'",
                file="tag_map.yaml",
            )


def _validate_counts_real(
    tags: dict[str, TagMeta], sources: list[SourceDef]
) -> None:
    counts: Counter[str] = Counter()
    for meta in tags.values():
        counts[meta.source_id] += 1
    for src in sources:
        actual = counts[src.id]
        if abs(actual - src.tag_count_expected) > COUNT_TOLERANCE:
            raise SemanticPackError(
                f"source '{src.id}': expected {src.tag_count_expected} tags, "
                f"got {actual} (tolerance ±{COUNT_TOLERANCE})",
                file="vessel.yaml",
            )


def _validate_native_map(
    native: NativeMap | None, tags: dict[str, TagMeta]
) -> None:
    if native is None:
        return
    seen: set[str] = set()
    for mapping in native.mappings:
        if mapping.native_id in seen:
            raise SemanticPackError(
                f"duplicate native_id '{mapping.native_id}'",
                file="native_map_stub.yaml",
            )
        seen.add(mapping.native_id)
        if mapping.tag_id not in tags:
            # orphan native_id -> warning only (plan §802)
            log.warning(
                "native_map_stub.yaml: native_id '%s' references unknown tag '%s' "
                "(stub mode warning)",
                mapping.native_id,
                mapping.tag_id,
            )


# --------------------------------------------------------------------------- #
# Checksum
# --------------------------------------------------------------------------- #

def _checksum(file_contents: dict[str, str]) -> str:
    h = hashlib.sha256()
    for name in sorted(file_contents):
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(file_contents[name].encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Pydantic error → SemanticPackError
# --------------------------------------------------------------------------- #

def _raise_pydantic(
    exc: ValidationError, file: str, *, hint: str | None = None
) -> None:
    err = exc.errors()[0]
    loc = ".".join(str(p) for p in err.get("loc", []) if p)
    msg = err.get("msg", "validation error")
    prefix = f"{hint}: " if hint else ""
    raise SemanticPackError(
        f"{prefix}{loc}: {msg}" if loc else f"{prefix}{msg}",
        file=file,
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def load_pack(pack_dir: Path | str) -> SemanticPack:
    """Load and validate a ship-pack directory.

    Parameters
    ----------
    pack_dir
        Directory containing ``vessel.yaml``, ``assets.yaml``, ``tag_map.yaml``
        and optionally ``native_map_stub.yaml``.

    Returns
    -------
    SemanticPack
        Frozen, validated, checksummed view of the pack.

    Raises
    ------
    SemanticPackError
        On any structural or cross-reference problem (fail-fast).
    """
    pack_dir = Path(pack_dir)
    if not pack_dir.is_dir():
        raise SemanticPackError(f"pack dir not found: {pack_dir}")

    raw_files: dict[str, str] = {}
    parsed: dict[str, Any] = {}

    for name in REQUIRED_FILES:
        path = pack_dir / name
        if not path.is_file():
            raise SemanticPackError(f"missing required file '{name}'")
        text = path.read_text(encoding="utf-8")
        raw_files[name] = text
        parsed[name] = _read_yaml(path)

    for name in OPTIONAL_FILES:
        path = pack_dir / name
        if path.is_file():
            raw_files[name] = path.read_text(encoding="utf-8")
            parsed[name] = _read_yaml(path)

    # vessel.yaml
    vessel, sources = _load_vessel(parsed["vessel.yaml"])

    # assets.yaml -> tree
    engine_rooms_raw = parsed["assets.yaml"].get("engine_rooms")
    if engine_rooms_raw is None:
        raise SemanticPackError("missing 'engine_rooms' mapping", file="assets.yaml")
    root = _build_tree(engine_rooms_raw)

    # tag_map.yaml
    tags = _load_tag_map(parsed["tag_map.yaml"])

    # cross-file invariants
    _validate_uniqueness(root)
    _validate_tag_refs(tags, root, sources)
    _validate_counts_real(tags, sources)

    # native map (optional)
    native = None
    if "native_map_stub.yaml" in parsed:
        native = _load_native_map(parsed["native_map_stub.yaml"])
    _validate_native_map(native, tags)

    checksum = _checksum(raw_files)

    return SemanticPack(
        vessel_id=vessel.id,
        name=vessel.name,
        imo=vessel.imo,
        pack_version=vessel.pack_version,
        sources=sources,
        root=root,
        tags=tags,
        native_map=native,
        checksum=checksum,
        raw={
            "vessel.yaml": parsed["vessel.yaml"],
            "assets.yaml": parsed["assets.yaml"],
            "tag_map.yaml": parsed["tag_map.yaml"],
        },
    )
