from __future__ import annotations

import asyncio

import pytest

from app.telemetry.models import Quality


@pytest.mark.asyncio
async def test_collector_subscribes_to_emulator_into_canonical_samples(
    opcua_integration: tuple[object, object, object],
) -> None:
    """B3 subscribes to a live OPC UA emulator → good canonical samples."""
    connector, sink, _emulator = opcua_integration  # type: ignore[misc]
    try:
        await connector.connect()
        await connector.subscribe(
            ["ns=2;s=AI4104", "ns=2;s=AI4101"],
            sink.raw_callback,
        )
        sink.sample_event.clear()

        await asyncio.wait_for(sink.sample_event.wait(), timeout=5.0)
        await asyncio.sleep(0.1)

        assert sink.samples
        by_tag = {sample.tag_id: sample for sample in sink.samples}
        assert {"TAI4101", "TAI4104"} <= by_tag.keys()
        assert all(
            sample.quality is Quality.GOOD
            for sample in sink.samples
            if sample.value is not None
        )
        assert by_tag["TAI4104"].value == pytest.approx(1800.0, abs=1e-3)
    finally:
        await connector.disconnect()
