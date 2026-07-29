from __future__ import annotations

import asyncio
import inspect
import logging
import ssl
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from collector.config.models import MqttSourceConfig
from collector.core.restart_policy import RestartPolicy
from collector.util.backoff import compute_backoff
from collector.util.time import utc_now

logger = logging.getLogger(__name__)

OnMqttMessage = Callable[[str, bytes, datetime], Awaitable[None] | None]
ClientFactory = Callable[[], Any]

__all__ = [
    "AsyncMqttClient",
    "MqttConnectionError",
    "MqttSubscribeError",
    "OnMqttMessage",
]


class MqttConnectionError(Exception):
    """Ошибка подключения или восстановления MQTT-сессии."""


class MqttSubscribeError(Exception):
    """Ошибка подписки на MQTT topic filter."""


class AsyncMqttClient:
    """Subscribe-only async wrapper around aiomqtt.

    Wrapper forwards raw topic and bytes payload. JSON and semantic parsing are
    intentionally left to the connector layer.
    """

    def __init__(
        self,
        config: MqttSourceConfig,
        client_factory: ClientFactory | None = None,
        *,
        on_message: OnMqttMessage | None = None,
        policy: RestartPolicy | None = None,
    ) -> None:
        self.config = config
        self._client_factory = client_factory or self._make_client
        self._on_message = on_message
        self._policy = policy or RestartPolicy()
        self._subscriptions: dict[str, int] = {}
        self._client: Any | None = None
        self._connection: Any | None = None
        self._task: asyncio.Task[None] | None = None
        self._stop_requested = False
        self._connected = False

    def is_connected(self) -> bool:
        """Return whether an active MQTT session is available."""
        return self._connected

    async def connect(self) -> None:
        """Connect once and start the background receive/reconnect task."""
        if self._connected or (
            self._task is not None and not self._task.done()
        ):
            return

        self._stop_requested = False
        try:
            await self._open_connection()
        except Exception as exc:
            await self._close_connection()
            raise MqttConnectionError(
                f"failed to connect MQTT source {self.config.id}"
            ) from exc

        await self.subscribe(
            self.config.subscribe.topic_prefix,
            qos=self.config.subscribe.qos,
        )
        self._task = asyncio.create_task(
            self._run_receive_loop(),
            name=f"mqtt-client-{self.config.id}",
        )

    async def disconnect(self) -> None:
        """Stop receiving and close the MQTT session idempotently."""
        self._stop_requested = True
        task = self._task
        self._task = None
        if task is not None and task is not asyncio.current_task():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self._close_connection()

    async def subscribe(self, topic_filter: str, qos: int = 0) -> None:
        """Subscribe to a topic filter and replay it after reconnect."""
        if not self.is_connected() or self._client is None:
            raise MqttSubscribeError("MQTT client is not connected")
        if self._subscriptions.get(topic_filter) == qos:
            return

        try:
            await self._client.subscribe(topic_filter, qos=qos)
        except Exception as exc:
            raise MqttSubscribeError(
                f"failed to subscribe to {topic_filter!r}"
            ) from exc
        self._subscriptions[topic_filter] = qos

    async def _open_connection(self) -> None:
        connection = self._client_factory()
        client = await connection.__aenter__()
        self._connection = connection
        self._client = client
        self._connected = True
        try:
            for topic_filter, qos in self._subscriptions.items():
                await client.subscribe(topic_filter, qos=qos)
        except Exception:
            await self._close_connection()
            raise

    async def _close_connection(self) -> None:
        connection = self._connection
        self._connection = None
        self._client = None
        self._connected = False
        if connection is not None:
            await connection.__aexit__(None, None, None)

    async def _run_receive_loop(self) -> None:
        attempt = 0
        while not self._stop_requested:
            try:
                if not self._connected:
                    await self._open_connection()
                    attempt = 0

                messages = getattr(self._client, "messages", None)
                if not hasattr(messages, "__aiter__"):
                    messages = self._client
                async for message in messages:
                    await self._dispatch_message(message)
                if not self._stop_requested:
                    raise MqttConnectionError("MQTT message stream closed")
            except asyncio.CancelledError:
                raise
            except Exception:
                await self._close_connection()
                if self._stop_requested:
                    return
                await asyncio.sleep(compute_backoff(attempt, self._policy))
                attempt += 1

    async def _dispatch_message(self, message: Any) -> None:
        if self._on_message is None:
            return
        topic_raw = getattr(message, "topic", None)
        payload = getattr(message, "payload", None)
        if topic_raw is None or not isinstance(payload, (bytes, bytearray)):
            return
        topic = topic_raw if isinstance(topic_raw, str) else str(topic_raw)
        if not topic:
            return
        payload_bytes = bytes(payload)

        try:
            callback = self._on_message
            recv_ts = utc_now()
            if inspect.iscoroutinefunction(callback):
                await callback(topic, payload_bytes, recv_ts)
            else:
                await asyncio.to_thread(callback, topic, payload_bytes, recv_ts)
        except Exception:
            logger.exception("MQTT message callback failed")

    def _make_client(self) -> Any:
        try:
            import aiomqtt
        except ImportError as exc:
            raise MqttConnectionError(
                "aiomqtt dependency is not installed"
            ) from exc

        connection_config = self.config.connection
        kwargs: dict[str, Any] = {
            "hostname": connection_config.host,
            "port": connection_config.port,
            "identifier": connection_config.client_id,
            "username": connection_config.username,
            "password": connection_config.password,
        }
        if connection_config.tls:
            kwargs["tls_context"] = ssl.create_default_context(
                cafile=connection_config.ca_cert
            )
        return aiomqtt.Client(**kwargs)
