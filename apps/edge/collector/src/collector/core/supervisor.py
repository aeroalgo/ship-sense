from __future__ import annotations

import asyncio
import contextlib
import logging

from collector.core.restart_policy import RestartPolicy
from collector.domain.errors import ConnectError
from collector.domain.interfaces import SourceConnector, Subscription
from collector.domain.raw_models import RawSample
from collector.domain.health_models import SourceState
from collector.util.backoff import compute_backoff

logger = logging.getLogger(__name__)


class SourceSupervisor:
    """Жизненный цикл одного источника.

    connect → subscribe → reconnect по политике (RestartPolicy).
    Один asyncio.Task на источник (ADR-COL-002). Сбой одного источника
    не останавливает другие (AC-B1-04): task-продюсеры независимы,
    общая raw_queue.
    """

    def __init__(
        self,
        connector: SourceConnector,
        raw_queue: asyncio.Queue[RawSample],
        policy: RestartPolicy,
        native_ids: list[str],
    ) -> None:
        self._connector = connector
        self._raw_queue = raw_queue
        self._policy = policy
        self._native_ids = native_ids
        self._task: asyncio.Task[None] | None = None
        self._consecutive_failures = 0
        self._state: SourceState = SourceState.RECONNECTING
        self._subscription: Subscription | None = None
        self._stopped = False

    @property
    def state(self) -> SourceState:
        return self._state

    async def healthcheck(self):
        status = await self._connector.healthcheck()
        return status.model_copy(update={"state": self._state})

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(
            self._run(), name=f"source:{self._connector.source_id}"
        )

    async def stop(self) -> None:
        """cancel task → await → disconnect (однократно)."""
        if self._stopped:
            return
        self._stopped = True
        if self._task is not None and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        with contextlib.suppress(Exception):
            await self._connector.disconnect()

    async def _run(self) -> None:
        try:
            await self._supervise()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception(
                "source:%s supervisor exited unexpectedly",
                self._connector.source_id,
            )

    async def _supervise(self) -> None:
        while True:
            if self._is_cold():
                self._state = SourceState.DOWN
                await asyncio.sleep(0.1)
                continue

            connected = await self._try_connect()
            if not connected:
                if self._is_cold():
                    continue
                await self._sleep_backoff()
                continue

            subscribed = await self._try_subscribe()
            if not subscribed:
                # connect успел — оборвать transport перед backoff
                with contextlib.suppress(Exception):
                    await self._connector.disconnect()
                if self._is_cold():
                    continue
                await self._sleep_backoff()
                continue

            # Жизнь: ждём, пока подписка не умрёт (cancel/разрыв).
            self._state = SourceState.UP
            await self._wait_until_dead(self._subscription)
            # Подписка порвалась → failure → reconnect.
            if self._is_cold():
                continue
            await self._sleep_backoff()

    def _is_cold(self) -> bool:
        limit = self._policy.max_consecutive_failures
        return limit is not None and self._consecutive_failures >= limit

    async def _try_connect(self) -> bool:
        self._state = SourceState.RECONNECTING
        try:
            await self._connector.connect()
        except asyncio.CancelledError:
            raise
        except (ConnectError, Exception):  # noqa: BLE001
            self._fail()
            return False
        return True

    async def _try_subscribe(self) -> bool:
        try:
            self._subscription = await self._connector.subscribe(
                self._native_ids, self._on_sample
            )
        except asyncio.CancelledError:
            raise
        except (ConnectError, Exception):  # noqa: BLE001
            self._fail()
            return False
        return True

    def _fail(self) -> None:
        self._consecutive_failures += 1

    async def _sleep_backoff(self) -> None:
        self._state = SourceState.RECONNECTING
        await asyncio.sleep(
            compute_backoff(self._consecutive_failures, self._policy)
        )

    async def _wait_until_dead(
        self, subscription: Subscription | None
    ) -> None:
        if subscription is None:
            return
        await subscription.cancel_event.wait()

    async def _on_sample(self, sample: RawSample) -> None:
        # Первый сэмпл после восстановления = подписка жива.
        self._consecutive_failures = 0
        await self._raw_queue.put(sample)
