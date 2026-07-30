from __future__ import annotations

import asyncio
import pytest

from app.telemetry.models import Quality


@pytest.mark.asyncio
async def test_collector_reads_emulator_into_canonical_sink(
    modbus_integration: tuple[object, object],
) -> None:
    """Collector B2 reads a live emulator and emits good canonical samples."""
    connector, sink = modbus_integration  # type: ignore[misc]
    try:
        await connector.connect()
        await connector.subscribe(
            ["40101", "40107"],
            sink.raw_callback,
        )
        sink.sample_event.clear()

        await asyncio.wait_for(sink.sample_event.wait(), timeout=3.0)
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
