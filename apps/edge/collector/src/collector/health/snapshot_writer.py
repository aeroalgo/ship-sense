"""SnapshotWriter — periodic JSON health dump (AC-HLT-02)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from collector.domain.models import CollectorHealthSnapshot

logger = logging.getLogger(__name__)
SnapshotFactory = Callable[[], Awaitable[CollectorHealthSnapshot]]


class SnapshotWriter:
    """Пишет CollectorHealthSnapshot в JSON-файл."""

    def __init__(self, *, path: Path, interval_sec: float = 5) -> None:
        self._path = path
        self._interval_sec = interval_sec
        self._task: asyncio.Task[None] | None = None

    @property
    def path(self) -> Path:
        return self._path

    @property
    def interval_sec(self) -> float:
        return self._interval_sec

    async def start(self, snapshot_factory: SnapshotFactory) -> None:
        """Write an initial snapshot and refresh it until stopped."""
        if self._task is not None:
            return
        await self._write_snapshot(snapshot_factory)
        self._task = asyncio.create_task(
            self._loop(snapshot_factory), name="collector-health-snapshot"
        )

    async def stop(self) -> None:
        """Stop periodic writes; the final snapshot is written by the app."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _loop(self, snapshot_factory: SnapshotFactory) -> None:
        while True:
            await asyncio.sleep(self._interval_sec)
            await self._write_snapshot(snapshot_factory)

    async def _write_snapshot(self, snapshot_factory: SnapshotFactory) -> None:
        try:
            self.write(await snapshot_factory())
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError, RuntimeError):
            logger.exception("health snapshot write failed")

    def write(self, snapshot: CollectorHealthSnapshot) -> None:
        """Сериализовать snapshot в JSON и записать в файл."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = snapshot.model_dump(mode="json")
        self._path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

