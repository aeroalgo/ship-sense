from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from collector.core.restart_policy import RestartPolicy
from collector.core.supervisor import SourceSupervisor
from collector.domain.errors import ConnectError
from collector.domain.interfaces import OnSampleCallback, Subscription
from collector.domain.models import (
    HealthStatus,
    RawSample,
    RawTagDescriptor,
    SourceState,
)
from collector.util.backoff import compute_backoff


UTC_NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------
# Pure-function backoff tests (AC-B1-05)
# ---------------------------------------------------------------


def test_backoff_jitter_off_matches_exponential_formula() -> None:
    policy = RestartPolicy(jitter=False)

    assert [compute_backoff(a, policy) for a in range(0, 8)] == [
        1.0,
        2.0,
        4.0,
        8.0,
        16.0,
        32.0,
        60.0,
        60.0,
    ]


def test_backoff_capped_at_max_regardless_of_attempt() -> None:
    policy = RestartPolicy(
        initial_backoff_sec=1.0, max_backoff_sec=60.0, jitter=False
    )

    for attempt in (100, 1_000, 100_000):
        assert compute_backoff(attempt, policy) == 60.0


def test_backoff_jitter_on_stays_within_range() -> None:
    policy = RestartPolicy(jitter=True)

    for attempt in range(0, 12):
        upper = min(
            policy.initial_backoff_sec * (2**attempt),
            policy.max_backoff_sec,
        )
        for _ in range(200):
            delay = compute_backoff(attempt, policy)
            assert 0.0 <= delay <= upper


def test_backoff_jitter_off_is_deterministic() -> None:
    policy = RestartPolicy(jitter=False)

    for attempt in range(0, 10):
        first = compute_backoff(attempt, policy)
        second = compute_backoff(attempt, policy)
        assert first == second


def test_restart_policy_defaults_match_plan() -> None:
    policy = RestartPolicy()

    assert policy.initial_backoff_sec == 1.0
    assert policy.max_backoff_sec == 60.0
    assert policy.max_consecutive_failures is None
    assert policy.jitter is True


# ---------------------------------------------------------------
# Fake connector — для supervisor-тестов
# ---------------------------------------------------------------


class _FakeConnector:
    """Конфигурируемый fake: падает/пушит по сценарию."""

    def __init__(
        self,
        source_id: str,
        *,
        connect_fails: int = 0,
        subscribe_fails: int = 0,
        native_ids: list[str] | None = None,
    ) -> None:
        self.source_id = source_id
        self.protocol = "fake"
        self._connect_fails = connect_fails
        self._subscribe_fails = subscribe_fails
        self._connect_calls = 0
        self._subscribe_calls = 0
        self._disconnect_calls = 0
        self._native_ids = native_ids or ["40101"]
        self._reconnect_count = 0
        self._last_ok_ts: datetime | None = None
        self._on_sample: OnSampleCallback | None = None
        self._alive = asyncio.Event()

    async def connect(self) -> None:
        self._connect_calls += 1
        if self._connect_calls <= self._connect_fails:
            self._reconnect_count += 1
            raise ConnectError(f"{self.source_id}: connect fails")

    async def discover_tags(self) -> list[RawTagDescriptor]:
        return []

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        return []

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        self._subscribe_calls += 1
        if self._subscribe_calls <= self._subscribe_fails:
            self._reconnect_count += 1
            raise ConnectError(f"{self.source_id}: subscribe fails")
        self._on_sample = on_sample
        self._alive.set()
        sub = Subscription(
            id=f"sub-{self.source_id}", tag_ids=list(native_ids)
        )
        return sub

    async def healthcheck(self) -> HealthStatus:
        state = SourceState.UP if self._alive.is_set() else SourceState.DOWN
        return HealthStatus(
            source_id=self.source_id,
            state=state,
            last_ok_ts=self._last_ok_ts,
            reconnect_count=self._reconnect_count,
        )

    async def disconnect(self) -> None:
        self._disconnect_calls += 1
        self._on_sample = None
        self._alive.clear()

    async def push_sample(self, value: int = 1) -> None:
        assert self._on_sample is not None
        await self._on_sample(
            RawSample(
                source_id=self.source_id,
                native_id=self._native_ids[0],
                raw_value=value,
                recv_ts=UTC_NOW,
            )
        )

    @property
    def disconnect_calls(self) -> int:
        return self._disconnect_calls


def _new_supervisor(
    connector: _FakeConnector,
    *,
    policy: RestartPolicy | None = None,
    queue: asyncio.Queue[RawSample] | None = None,
) -> SourceSupervisor:
    return SourceSupervisor(
        connector,  # type: ignore[arg-type]
        queue if queue is not None else asyncio.Queue(),
        policy if policy is not None else RestartPolicy(jitter=False),
        native_ids=["40101"],
    )


# ---------------------------------------------------------------
# Supervisor lifecycle tests
# (AC-B1-04, AC-B1-05, AC-HLT-04)
# ---------------------------------------------------------------


def test_supervisor_forwards_samples_to_raw_queue() -> None:
    async def scenario() -> None:
        connector = _FakeConnector("aps_main")
        queue: asyncio.Queue[RawSample] = asyncio.Queue()
        sup = _new_supervisor(connector, queue=queue)
        await sup.start()
        try:
            await asyncio.wait_for(connector._alive.wait(), timeout=1.0)
            await connector.push_sample(value=42)
            sample = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert sample.source_id == "aps_main"
            assert sample.raw_value == 42
        finally:
            await sup.stop()

    asyncio.run(scenario())


def test_stop_cancels_task_and_disconnects_once() -> None:
    async def scenario() -> None:
        connector = _FakeConnector("aps_main")
        sup = _new_supervisor(connector)
        await sup.start()
        await asyncio.wait_for(connector._alive.wait(), timeout=1.0)

        await sup.stop()

        assert connector.disconnect_calls == 1
        assert sup._task is not None and sup._task.done()

    asyncio.run(scenario())


def test_stop_is_idempotent() -> None:
    async def scenario() -> None:
        connector = _FakeConnector("aps_main")
        sup = _new_supervisor(connector)
        await sup.start()
        await asyncio.wait_for(connector._alive.wait(), timeout=1.0)

        await sup.stop()
        await sup.stop()

        assert connector.disconnect_calls == 1

    asyncio.run(scenario())


def test_stop_before_start_still_disconnects() -> None:
    async def scenario() -> None:
        connector = _FakeConnector("aps_main")
        sup = _new_supervisor(connector)

        await sup.stop()

        assert connector.disconnect_calls == 1

    asyncio.run(scenario())


def test_dual_source_isolation_killing_a_keeps_b_pushing() -> None:
    """AC-B1-04: падение source A не роняет поток source B."""

    async def scenario() -> None:
        connector_a = _FakeConnector("aps_main", subscribe_fails=10**9)
        connector_b = _FakeConnector("skt_geu")
        queue: asyncio.Queue[RawSample] = asyncio.Queue()
        policy = RestartPolicy(initial_backoff_sec=0.001, jitter=False)
        sup_a = _new_supervisor(connector_a, queue=queue, policy=policy)
        sup_b = _new_supervisor(connector_b, queue=queue, policy=policy)
        await sup_a.start()
        await sup_b.start()
        try:
            await asyncio.wait_for(connector_b._alive.wait(), timeout=1.0)
            await connector_b.push_sample(value=7)
            sample = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert sample.source_id == "skt_geu"
            await connector_b.push_sample(value=8)
            sample_b = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert sample_b.source_id == "skt_geu"
            assert sample_b.raw_value == 8
        finally:
            await sup_a.stop()
            await sup_b.stop()

    asyncio.run(scenario())


def test_reconnect_resets_counter_on_first_sample() -> None:
    """AC-B1-05: counter сбрасывается на connect+sample."""

    async def scenario() -> None:
        connector = _FakeConnector("aps_main", connect_fails=2)
        policy = RestartPolicy(initial_backoff_sec=0.001, jitter=False)
        sup = _new_supervisor(connector, policy=policy)
        await sup.start()
        try:
            await asyncio.wait_for(connector._alive.wait(), timeout=1.0)
            await connector.push_sample()
            assert connector._connect_calls >= 3
            assert sup._consecutive_failures == 0
        finally:
            await sup.stop()

    asyncio.run(scenario())


def test_reconnect_with_backoff_eventually_recovers() -> None:
    """AC-B1-05: backoff, recovery после неудач."""

    async def scenario() -> None:
        connector = _FakeConnector("aps_main", connect_fails=3)
        policy = RestartPolicy(initial_backoff_sec=0.001, jitter=False)
        sup = _new_supervisor(connector, policy=policy)
        await sup.start()
        try:
            await asyncio.wait_for(connector._alive.wait(), timeout=1.0)
            assert connector._connect_calls == 4
            assert connector._alive.is_set()
        finally:
            await sup.stop()

    asyncio.run(scenario())


def test_max_consecutive_failures_moves_to_down() -> None:
    """AC-B1-06: при max_consecutive_failures → DOWN (cold)."""

    async def scenario() -> None:
        connector = _FakeConnector("aps_main", connect_fails=10**9)
        policy = RestartPolicy(
            initial_backoff_sec=0.001,
            jitter=False,
            max_consecutive_failures=3,
        )
        sup = _new_supervisor(connector, policy=policy)
        await sup.start()
        try:
            await asyncio.sleep(0.1)
            assert sup.state is SourceState.DOWN
            assert connector._connect_calls == 3
        finally:
            await sup.stop()

    asyncio.run(scenario())


def test_subscribe_failure_disconnects_before_backoff() -> None:
    """connect OK, subscribe падает → disconnect перед backoff."""

    async def scenario() -> None:
        connector = _FakeConnector("aps_main", subscribe_fails=10**9)
        policy = RestartPolicy(initial_backoff_sec=0.001, jitter=False)
        sup = _new_supervisor(connector, policy=policy)
        await sup.start()
        try:
            await asyncio.sleep(0.1)
            assert connector._disconnect_calls >= 1
        finally:
            await sup.stop()

    asyncio.run(scenario())


def test_shutdown_does_not_count_as_failure() -> None:
    async def scenario() -> None:
        connector = _FakeConnector("aps_main")
        sup = _new_supervisor(connector)
        await sup.start()
        await asyncio.wait_for(connector._alive.wait(), timeout=1.0)

        await sup.stop()

        assert sup._consecutive_failures == 0

    asyncio.run(scenario())


def test_subscribe_failure_isolated_across_sources() -> None:
    """AC-B1-04: A падает в subscribe, B жив и пушит."""

    async def scenario() -> None:
        connector_a = _FakeConnector("aps_main", subscribe_fails=10**9)
        connector_b = _FakeConnector("skt_geu")
        queue: asyncio.Queue[RawSample] = asyncio.Queue()
        policy = RestartPolicy(initial_backoff_sec=0.001, jitter=False)
        sup_a = _new_supervisor(connector_a, queue=queue, policy=policy)
        sup_b = _new_supervisor(connector_b, queue=queue, policy=policy)
        await sup_a.start()
        await sup_b.start()
        try:
            await asyncio.wait_for(connector_b._alive.wait(), timeout=1.0)
            await connector_b.push_sample(value=99)
            sample = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert sample.source_id == "skt_geu"
            assert sample.raw_value == 99
        finally:
            await sup_a.stop()
            await sup_b.stop()
            assert connector_a.disconnect_calls >= 1
            assert connector_b.disconnect_calls == 1

    asyncio.run(scenario())
