"""SemanticEngine (s13).

In-memory tree + indexes over SemanticPack.
Pure state computation for TagDisplayState / AggregateStatus.
diff_native_map hook + internal quarantine snapshot (persist delegated to s15).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable

from app.semantic.loader import load_pack
from app.semantic.models import (
    AggregateStatus,
    AssetNode,
    NativeMap,
    QuarantineEntry,
    QuarantineKind,
    QuarantineReport,
    SemanticPack,
    TagDisplayState,
    TagMeta,
)
from . import quarantine as _qmod


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class _TagPath:
    mechanism_id: str
    system_id: str
    engine_room_id: str


class SemanticEngine:
    """In-memory semantic index + state machine.

    Thread-unsafe by design (single writer startup + read-only after load).
    """

    def __init__(self, *, now_provider: Callable[[], datetime] | None = None) -> None:
        self._now: Callable[[], datetime] = now_provider or _default_now
        self._pack: SemanticPack | None = None
        self._root: AssetNode | None = None
        self._tags: dict[str, TagMeta] = {}
        self._mech_to_tags: dict[str, list[str]] = {}
        self._tag_to_mech: dict[str, str] = {}
        self._node_index: dict[str, AssetNode] = {}  # id -> node for fast lookup
        self._quarantined: set[str] = set()  # unacknowledged only (s15 will persist)
        self._last_sample_ts: dict[str, datetime] = {}
        self._approved_native: NativeMap | None = None
        self._invalid: bool = False  # global stop flag (set only on bad load in future)

    # ------------------------------------------------------------------ #
    # Load
    # ------------------------------------------------------------------ #

    def load(self, pack_dir: Path | str) -> None:
        """Load pack, build indexes. Replaces previous state."""
        pack = load_pack(pack_dir)
        self._pack = pack
        self._root = pack.root
        self._tags = dict(pack.tags)
        self._build_indexes(pack.root)
        self._approved_native = pack.native_map
        self._quarantined.clear()
        self._last_sample_ts.clear()
        self._invalid = False

    def _build_indexes(self, root: AssetNode) -> None:
        self._mech_to_tags.clear()
        self._tag_to_mech.clear()
        self._node_index.clear()

        def walk(node: AssetNode, er: str = "", sys: str = "") -> None:
            self._node_index[node.id] = node
            if node.kind.value == "engine_room":
                er = node.id
            elif node.kind.value == "system":
                sys = node.id
            elif node.kind.value == "mechanism":
                self._mech_to_tags[node.id] = list(node.tags)
                for t in node.tags:
                    self._tag_to_mech[t] = node.id
            for ch in node.children:
                walk(ch, er, sys)
            # also index tags list on mechanism node itself
            if node.tags:
                self._node_index.setdefault(node.id, node)

        walk(root)
        # ensure vessel itself
        if root.id:
            self._node_index[root.id] = root

    # ------------------------------------------------------------------ #
    # Navigation (post-load)
    # ------------------------------------------------------------------ #

    def get_tree(self) -> AssetNode:
        if self._root is None:
            raise RuntimeError("SemanticEngine not loaded")
        return self._root

    def get_tag_meta(self, tag_id: str) -> TagMeta:
        if tag_id not in self._tags:
            raise KeyError(tag_id)
        return self._tags[tag_id]

    def get_mechanism_tags(self, mechanism_id: str) -> list[str]:
        return list(self._mech_to_tags.get(mechanism_id, []))

    # ------------------------------------------------------------------ #
    # Aggregate status (worst-of)
    # ------------------------------------------------------------------ #

    def aggregate_status(self, node_id: str) -> AggregateStatus:
        if self._root is None:
            raise RuntimeError("SemanticEngine not loaded")
        if node_id not in self._node_index:
            # unknown node -> treat as normal (or raise? lean: normal for missing subtree)
            return AggregateStatus.NORMAL

        node = self._node_index[node_id]
        worst = self._worst_for_node(node)
        return worst

    def _worst_for_node(self, node: AssetNode) -> AggregateStatus:
        # collect states from direct tags + children
        states: list[AggregateStatus] = []
        for tag in node.tags:
            st = self._project_tag_to_aggregate(self.get_tag_state(tag))
            states.append(st)
        for ch in node.children:
            states.append(self._worst_for_node(ch))
        if not states:
            return AggregateStatus.NORMAL
        return self._worst_of(states)

    @staticmethod
    def _project_tag_to_aggregate(state: TagDisplayState) -> AggregateStatus:
        if state is TagDisplayState.QUARANTINE:
            return AggregateStatus.QUARANTINE
        if state is TagDisplayState.NO_DATA:
            return AggregateStatus.NO_DATA
        # stale is per-tag hint, does not force mechanism to no_data
        return AggregateStatus.NORMAL

    @staticmethod
    def _worst_of(candidates: list[AggregateStatus]) -> AggregateStatus:
        order = [
            AggregateStatus.CRITICAL,
            AggregateStatus.WARNING,
            AggregateStatus.QUARANTINE,
            AggregateStatus.NO_DATA,
            AggregateStatus.NORMAL,
        ]
        # lower index = more severe (worst)
        worst_idx = min((order.index(c) for c in candidates if c in order), default=len(order) - 1)
        return order[worst_idx]

    # ------------------------------------------------------------------ #
    # Tag state (precedence per CR-STO-03)
    # ------------------------------------------------------------------ #

    def get_tag_state(self, tag_id: str) -> TagDisplayState:
        if self._invalid:
            return TagDisplayState.STOP
        if tag_id not in self._tags:
            # unknown tag in live context -> treat as no_data (no quarantine auto)
            return TagDisplayState.NO_DATA

        # 1. quarantine (unacked)
        if tag_id in self._quarantined:
            return TagDisplayState.QUARANTINE

        meta = self._tags[tag_id]
        thresh = (meta.expected_rate_s or 30.0) * 3.0
        no_data_win = max(thresh * 3.0, 90.0)

        last = self._last_sample_ts.get(tag_id)
        if last is None:
            return TagDisplayState.NO_DATA

        age = (self._now() - last).total_seconds()
        if age > no_data_win:
            return TagDisplayState.NO_DATA
        if age > thresh:
            return TagDisplayState.STALE
        return TagDisplayState.NORMAL

    # ------------------------------------------------------------------ #
    # Test / writer hooks (in-mem snapshot)
    # ------------------------------------------------------------------ #

    def update_last_sample_ts(self, tag_id: str, ts: datetime) -> None:
        """Called by writer after successful sample persist (for state)."""
        self._last_sample_ts[tag_id] = ts

    # ------------------------------------------------------------------ #
    # Diff + acknowledge (s13 hook; full reconcile in s15)
    # ------------------------------------------------------------------ #

    def diff_native_map(self, new_map: NativeMap) -> QuarantineReport:
        """Delegate to pure diff (s15). Update local unacked cache for added/changed (real tags only)."""
        known = set(self._tags.keys())
        report = _qmod.diff_native_map(self._approved_native, new_map, known_tags=known)
        for e in list(report.added) + list(report.changed):
            if e.tag_id in self._tags:
                self._quarantined.add(e.tag_id)
        # removed: do not auto-quarantine; may become no_data later
        return report

    def acknowledge_quarantine(self, tag_id: str) -> None:
        """Local cache only. Persist + reload via quarantine.acknowledge(session) + refresh."""
        self._quarantined.discard(tag_id)

    def refresh_quarantine_from(self, tag_ids: Iterable[str]) -> None:
        """Replace local unacked cache from persisted source (called after apply/ack)."""
        self._quarantined.clear()
        for tid in tag_ids:
            if tid in self._tags:
                self._quarantined.add(tid)

    # ------------------------------------------------------------------ #
    # Introspection for tests / s15
    # ------------------------------------------------------------------ #

    @property
    def quarantined_tags(self) -> frozenset[str]:
        return frozenset(self._quarantined)

    def is_loaded(self) -> bool:
        return self._pack is not None
