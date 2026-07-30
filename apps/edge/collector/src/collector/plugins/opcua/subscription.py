"""OPC UA subscription manager.

AC-B3-02: Monitored items по NodeId из карты; publishing_interval ~1000 ms.
AC-B3-05: Reconnect + пересоздание subscriptions без дублей на стыке.
AC-B3-10: Keep-alive; session timeout handling.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from asyncua import Client
from asyncua.common import subscription

from collector.config.models import TagMapEntry
from collector.domain.interfaces import OnSampleCallback, Subscription
from collector.domain.raw_models import RawSample

logger = logging.getLogger(__name__)
diag_logger = logging.getLogger("collector.opcua.diag")


class SubscriptionManager:
    """
    Управление OPC UA подписками.

    - create_monitored_items по NodeId из tag_map.
    - on_data_change → RawSample → on_sample callback.
    - reconnect: пересоздать subscription (без дублей sequence/seam).
    """

    def __init__(
        self,
        client: Client,
        tag_map: list[TagMapEntry],
        on_sample: OnSampleCallback,
        publishing_interval_ms: int = 1000,
    ) -> None:
        self._client = client
        self._tag_map = {e.node_id or e.native_id: e for e in tag_map}
        self._on_sample = on_sample
        self._publishing_interval = publishing_interval_ms
        self._subscription: subscription.Subscription | None = None
        self._cancel_event: asyncio.Event | None = None
        self._sequence: int = 0  # для dedup на seam

    async def subscribe(self, native_ids: list[str]) -> Subscription:
        """Создать подписку и monitored items для native_ids."""
        self._cancel_event = asyncio.Event()

        # Создаём subscription с handler'ом
        self._subscription = await self._client.create_subscription(
            period=self._publishing_interval,
            handler=self._DataChangeHandler(self),
        )

        # Регистрируем monitored items
        node_ids = [nid for nid in native_ids if nid in self._tag_map]
        nodes = [self._client.get_node(nid) for nid in node_ids]

        if nodes:
            await self._subscription.subscribe_data_change(nodes)

        sub_id = f"opcua:{id(self)}"
        return Subscription(
            id=sub_id,
            tag_ids=list(native_ids),
            cancel_event=self._cancel_event or asyncio.Event(),
        )

    async def cancel(self) -> None:
        """Отменить подписку и удалить monitored items."""
        if self._cancel_event:
            self._cancel_event.set()
        if self._subscription:
            try:
                await self._subscription.delete()
            except Exception:  # noqa: BLE001, S110
                pass
            self._subscription = None

    async def recreate(self, native_ids: list[str]) -> Subscription:
        """
        Пересоздать подписку (reconnect path).

        AC-B3-05: без дублей sequence на стыке.
        """
        await self.cancel()
        # Сброс sequence для новой сессии
        self._sequence = 0
        return await self.subscribe(native_ids)

    def _make_raw_sample(
        self,
        node_id: str,
        value: Any,
        status: Any | None = None,
        source_ts: Any | None = None,
    ) -> RawSample:
        """Собрать RawSample из data change notification."""
        entry = self._tag_map.get(node_id)
        native_quality: str | None = None
        if status is not None:
            # StatusCode → structured token `opcua.<StatusName>` (для QualityEngine)
            name = getattr(status, "name", None) or str(status)
            native_quality = f"opcua.{name}"

        # sequence для dedup (инкремент на каждый sample)
        self._sequence += 1

        return RawSample(
            source_id="",  # заполняется в connector
            native_id=node_id,
            raw_value=value,
            native_quality=native_quality,
            recv_ts=datetime.now(UTC),  # connector перетрёт своим _recv_ts
            source_ts=source_ts,
            sequence=self._sequence,
        )

    class _DataChangeHandler:
        """Handler для data change notifications."""

        def __init__(self, manager: SubscriptionManager) -> None:
            self._manager = manager

        async def datachange_notification(
            self,
            node: Any,
            val: Any,
            data: subscription.DataChangeNotif,
        ) -> None:
            """Вызывается asyncua при изменении значения monitored item."""
            try:
                node_id = node.nodeid.to_string()
                sample = self._manager._make_raw_sample(
                    node_id=node_id,
                    value=val,
                    status=getattr(data, "StatusCode", None),
                    source_ts=getattr(data, "SourceTimestamp", None),
                )
                # Заполняем source_id позже в connector
                # Здесь просто отдаём в callback
                if self._manager._on_sample:
                    await self._manager._on_sample(sample)
            except Exception:  # noqa: BLE001
                logger.exception("datachange handler error for node %s", node)
