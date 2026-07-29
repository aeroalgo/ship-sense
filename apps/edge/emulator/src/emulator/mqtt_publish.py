"""CLI entrypoint: publish synthetic MQTT payloads via ``MqttPublisherAdapter``.

Run with::

    python -m emulator.mqtt_publish --broker mqtt://localhost:1883 --panels aps,geu

Reuses :class:`emulator.protocols.mqtt_publisher.MqttPublisherAdapter` — no payload
logic is duplicated here. This module only wires argparse → adapter lifecycle.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from collections.abc import Iterable
from typing import Any

from emulator.protocols.mqtt_publisher import MqttPublisherAdapter

_LOG = logging.getLogger("emulator.mqtt_publish")

_VALID_PANELS = ("aps", "geu")
_EXIT_BROKER_ERROR = 1


def _parse_panels(raw: str) -> list[str]:
    panels = [p.strip() for p in raw.split(",") if p.strip()]
    unknown = [p for p in panels if p not in _VALID_PANELS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown panel(s): {', '.join(unknown)}; valid: {', '.join(_VALID_PANELS)}"
        )
    if not panels:
        raise argparse.ArgumentTypeError("at least one panel required")
    return panels


def _positive_float(raw: str) -> float:
    value = float(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("interval must be positive")
    return value


def _nonneg_int(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("iterations must be >= 0")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m emulator.mqtt_publish",
        description="Publish deterministic synthetic MQTT payloads for the emulator.",
    )
    parser.add_argument(
        "--broker",
        default="mqtt://localhost:1883",
        help="Broker URL (default: mqtt://localhost:1883).",
    )
    parser.add_argument(
        "--panels",
        type=_parse_panels,
        default=["aps", "geu"],
        help="Comma-separated panel list, subset of {aps,geu} (default: aps,geu).",
    )
    parser.add_argument(
        "--interval",
        type=_positive_float,
        default=1.0,
        help="Seconds between publish ticks; must be > 0 (default: 1.0).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic RNG seed (default: 42).",
    )
    parser.add_argument(
        "--iterations",
        type=_nonneg_int,
        default=None,
        help="Number of publish ticks; omit to run until SIGTERM/SIGINT.",
    )
    return parser


def _make_adapter(panel: str, seed: int, interval: float) -> MqttPublisherAdapter:
    """Factory indirection — tests inject a mock here."""
    return MqttPublisherAdapter(panel=panel, seed=seed, interval=interval)


async def _run_all(
    adapters: Iterable[MqttPublisherAdapter],
    broker_url: str,
    iterations: int | None,
) -> None:
    """Connect all adapters, gather their publish loops, stop on completion/signal."""
    adapter_list = list(adapters)
    for adapter in adapter_list:
        await adapter.connect(broker_url)
    try:
        results = await asyncio.gather(
            *(a.publish_loop(iterations=iterations) for a in adapter_list),
            return_exceptions=True,
        )
    finally:
        for adapter in adapter_list:
            await adapter.stop()

    for adapter, result in zip(adapter_list, results, strict=True):
        if isinstance(result, BaseException):
            _LOG.error("panel %s publish loop failed: %r", adapter.panel, result)


def _install_signal_stoppers(
    loop: asyncio.AbstractEventLoop,
    adapters: list[MqttPublisherAdapter],
) -> None:
    def _stop_all(*_args: object) -> None:
        _LOG.info("signal received — stopping all publishers")
        for adapter in adapters:
            loop.create_task(adapter.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _stop_all, sig)
        except (NotImplementedError, RuntimeError):
            # signal handlers not supported (e.g. Windows / nested loop in tests)
            signal.signal(sig, lambda *_a: None)


async def amain(argv: list[str] | None = None) -> int:
    """Parse args, spin up adapters, publish until done or signalled. Returns exit code."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = build_parser().parse_args(argv)

    adapters = [
        _make_adapter(panel=panel, seed=args.seed, interval=args.interval)
        for panel in args.panels
    ]

    loop = asyncio.get_running_loop()
    _install_signal_stoppers(loop, adapters)

    try:
        await _run_all(adapters, broker_url=args.broker, iterations=args.iterations)
    except Exception as exc:  # noqa: BLE001 — top-level CLI boundary
        _LOG.error("mqtt_publish failed: %r", exc)
        return _EXIT_BROKER_ERROR
    return 0


def main() -> None:
    """Thin sync entrypoint."""
    try:
        import aiomqtt  # noqa: F401 — fail fast with a clear message
    except ImportError:
        sys.stderr.write(
            "aiomqtt is not installed. Install it with: pip install aiomqtt\n"
        )
        sys.exit(_EXIT_BROKER_ERROR)
    sys.exit(asyncio.run(amain()))


if __name__ == "__main__":
    main()
