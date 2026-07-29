from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from emulator.mqtt_publish import amain, build_parser


class FakeBroker:
    """Async-context-manager mock of an aiomqtt.Client-like object."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.connected = False
        self.closed = False

    async def __aenter__(self) -> "FakeBroker":
        self.connected = True
        return self

    async def __aexit__(self, *_args: object) -> None:
        self.connected = False
        self.closed = True

    async def publish(self, topic: str, payload: str, **_kwargs: object) -> None:
        self.messages.append((topic, payload))


def _factory(broker: FakeBroker):
    return lambda _host, _port: broker


# ---------------------------------------------------------------------------
# argparse
# ---------------------------------------------------------------------------


def test_parse_args_defaults() -> None:
    parser = build_parser()
    ns = parser.parse_args([])
    assert ns.broker == "mqtt://localhost:1883"
    assert ns.panels == ["aps", "geu"]
    assert ns.interval == pytest.approx(1.0)
    assert ns.seed == 42
    assert ns.iterations is None


def test_parse_args_custom_values() -> None:
    parser = build_parser()
    ns = parser.parse_args(
        ["--broker", "mqtt://broker:1883", "--panels", "geu", "--interval", "0.5",
         "--seed", "7", "--iterations", "3"]
    )
    assert ns.broker == "mqtt://broker:1883"
    assert ns.panels == ["geu"]
    assert ns.interval == pytest.approx(0.5)
    assert ns.seed == 7
    assert ns.iterations == 3


def test_parse_args_panels_strips_whitespace() -> None:
    parser = build_parser()
    ns = parser.parse_args(["--panels", " aps , geu "])
    assert ns.panels == ["aps", "geu"]


def test_parse_args_rejects_unknown_panel(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--panels", "foo"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "unknown panel" in captured.err.lower() or "invalid" in captured.err.lower()


def test_parse_args_rejects_nonpositive_interval(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--interval", "0"])
    assert exc.value.code == 2


# ---------------------------------------------------------------------------
# amain — publish behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_amain_publishes_at_least_one_message(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = FakeBroker()
    captured: dict[str, Any] = {}

    def fake_factory(panel: str, seed: int, interval: float) -> Any:
        from emulator.protocols.mqtt_publisher import MqttPublisherAdapter
        adapter = MqttPublisherAdapter(
            panel=panel, seed=seed, interval=interval, client_factory=_factory(broker)
        )
        captured.setdefault("adapter", adapter)
        return adapter

    monkeypatch.setattr("emulator.mqtt_publish._make_adapter", fake_factory)

    rc = await amain(
        ["--broker", "mqtt://x:1883", "--panels", "aps", "--iterations", "1"]
    )

    assert rc == 0
    assert len(broker.messages) >= 1
    topic, payload = broker.messages[0]
    assert topic.startswith("shipsense/v1/aps/")
    body = json.loads(payload)
    assert "@type" in body


@pytest.mark.asyncio
async def test_amain_publishes_multiple_panels(monkeypatch: pytest.MonkeyPatch) -> None:
    brokers: dict[str, FakeBroker] = {}

    def fake_factory(panel: str, seed: int, interval: float) -> Any:
        from emulator.protocols.mqtt_publisher import MqttPublisherAdapter
        broker = brokers.setdefault(panel, FakeBroker())
        return MqttPublisherAdapter(
            panel=panel, seed=seed, interval=interval, client_factory=_factory(broker)
        )

    monkeypatch.setattr("emulator.mqtt_publish._make_adapter", fake_factory)

    rc = await amain(["--panels", "aps,geu", "--iterations", "1"])

    assert rc == 0
    assert "aps" in brokers and "geu" in brokers
    assert brokers["aps"].messages, "aps broker got no messages"
    assert brokers["geu"].messages, "geu broker got no messages"
    assert brokers["aps"].closed and brokers["geu"].closed


@pytest.mark.asyncio
async def test_amain_returns_zero_on_iterations_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    broker = FakeBroker()

    def fake_factory(panel: str, seed: int, interval: float) -> Any:
        from emulator.protocols.mqtt_publisher import MqttPublisherAdapter
        return MqttPublisherAdapter(
            panel=panel, seed=seed, interval=interval, client_factory=_factory(broker)
        )

    monkeypatch.setattr("emulator.mqtt_publish._make_adapter", fake_factory)

    rc = await amain(["--panels", "aps", "--iterations", "2"])
    assert rc == 0
    # 2 iterations × 4 payload kinds = 8 publishes
    assert len(broker.messages) == 8


@pytest.mark.asyncio
async def test_amain_stops_on_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate SIGTERM by cancelling the running amain task."""
    broker = FakeBroker()

    def fake_factory(panel: str, seed: int, interval: float) -> Any:
        from emulator.protocols.mqtt_publisher import MqttPublisherAdapter
        return MqttPublisherAdapter(
            panel=panel, seed=seed, interval=0.01, client_factory=_factory(broker)
        )

    monkeypatch.setattr("emulator.mqtt_publish._make_adapter", fake_factory)

    task = asyncio.create_task(amain(["--panels", "aps"]))  # iterations=None → runs forever
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        rc = await task
    except asyncio.CancelledError:
        rc = None

    # Either it returned 0 via its own signal handling, or Cancelled propagated.
    # The point: no hang, no dangling tasks, broker closed.
    assert rc in (0, None)
    assert broker.closed
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    assert not tasks, f"dangling tasks: {tasks}"


@pytest.mark.asyncio
async def test_amain_unknown_panel_exits_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    """argparse type validation rejects unknown panel before adapter creation."""
    with pytest.raises(SystemExit) as exc:
        await amain(["--panels", "bogus"])
    assert exc.value.code == 2
