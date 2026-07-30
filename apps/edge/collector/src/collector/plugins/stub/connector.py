"""AC-B1-08: demo third-party stub plugin.

Demo-коннектор-заглушка: генерирует синтетические RawSample без реального
транспорта. Доказывает, что сторонний плагин регистрируется через import
side-effect без правки core registry.
"""

from __future__ import annotations

import asyncio
import itertools

from collector.config.models import SourceConfig
from collector.domain.interfaces import BaseSourceConnector, OnSampleCallback, Subscription
from collector.domain.raw_models import RawSample, RawTagDescriptor

STUB_DESCRIPTORS = (
    RawTagDescriptor(native_id="ai4101", name="stub_analog", unit="-"),
    RawTagDescriptor(native_id="di0101", name="stub_discrete", unit="-"),
)


class StubConnector(BaseSourceConnector):
    """Synthetic source: один RawSample на каждый запрошенный native_id."""

    def __init__(self, config: SourceConfig) -> None:
        super().__init__(config)
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def discover_tags(self) -> list[RawTagDescriptor]:
        return list(STUB_DESCRIPTORS)

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        return [self._sample(native_id) for native_id in native_ids]

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        cancel_event = asyncio.Event()

        async def _push() -> None:
            for native_id in native_ids:
                if cancel_event.is_set():
                    break
                await on_sample(self._sample(native_id))
            cancel_event.set()

        asyncio.create_task(_push())

        return Subscription(
            id=f"stub-{self.source_id}",
            tag_ids=list(native_ids),
            cancel_event=cancel_event,
        )

    async def disconnect(self) -> None:
        self._connected = False

    def _sample(self, native_id: str) -> RawSample:
        return RawSample(
            source_id=self.source_id,
            native_id=native_id,
            raw_value=0.0,
            native_quality="stub.synthetic",
            recv_ts=self._recv_ts(),
            source_ts=self._recv_ts(),
            sequence=next(_sequence),
        )


_sequence = itertools.count(1)
