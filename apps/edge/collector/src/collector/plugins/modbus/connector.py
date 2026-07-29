from __future__ import annotations

import asyncio
import logging
import os
from typing import Sequence

from collector.config.models import SourceConfig, TagMapEntry
from collector.domain.interfaces import BaseSourceConnector, OnSampleCallback, Subscription
from collector.domain.models import RawSample, RawTagDescriptor
from collector.plugins.modbus.client import AsyncModbusClient, ModbusClientError, ModbusTimeoutError
from collector.plugins.modbus.decoder import decode_float32, decode_int, extract_bit
from pymodbus.exceptions import ModbusException
from collector.plugins.modbus.poll_scheduler import PollGroup, PollScheduler

logger = logging.getLogger(__name__)
diag_logger = logging.getLogger("collector.modbus.diag")


class ModbusTcpConnector(BaseSourceConnector):
    """B2 ModbusTcpConnector: poll-based subscribe эмуляция.

    AC-B2-05/06/10, AC-B1-03/11.
    """

    def __init__(
        self,
        config: SourceConfig,
        client: AsyncModbusClient,
        tag_map: Sequence[TagMapEntry],
    ) -> None:
        super().__init__(config)
        self._client = client
        self._tag_map = list(tag_map)
        self._tag_by_native: dict[str, TagMapEntry] = {t.native_id: t for t in tag_map}
        self._tasks: list[asyncio.Task[None]] = []
        self._cancel_event: asyncio.Event | None = None
        self._on_sample: OnSampleCallback | None = None
        self._diag = bool(os.getenv("MODBUS_DEBUG"))

    async def connect(self) -> None:
        ok = await self._client.connect()
        if not ok:
            from collector.domain.errors import ConnectError

            raise ConnectError(f"failed to connect to {self._config.endpoint}")

    async def disconnect(self) -> None:
        # Отменить задачи подписки
        if self._cancel_event is not None:
            self._cancel_event.set()
        for t in self._tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        await self._client.disconnect()

    async def discover_tags(self) -> list[RawTagDescriptor]:
        return [
            RawTagDescriptor(
                native_id=t.native_id,
                name=t.tag_id,
                unit=t.unit,
                datatype=t.datatype,
            )
            for t in self._tag_map
        ]

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        samples: list[RawSample] = []
        for nid in native_ids:
            entry = self._tag_by_native.get(nid)
            if entry is None:
                samples.append(
                    RawSample(
                        source_id=self.source_id,
                        native_id=nid,
                        raw_value=None,
                        native_quality="unknown_tag",
                        recv_ts=self._recv_ts(),
                    )
                )
                continue
            try:
                regs = await self._read_registers(entry)
                value = self._decode(entry, regs)
                samples.append(
                    RawSample(
                        source_id=self.source_id,
                        native_id=nid,
                        raw_value=value,
                        recv_ts=self._recv_ts(),
                        native_quality="good",
                    )
                )
            except (ModbusClientError, ModbusTimeoutError) as e:
                samples.append(
                    RawSample(
                        source_id=self.source_id,
                        native_id=nid,
                        raw_value=None,
                        native_quality=_modbus_error_token(e),
                        recv_ts=self._recv_ts(),
                    )
                )
        return samples

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        self._on_sample = on_sample
        self._cancel_event = asyncio.Event()

        # Построить группы из подмножества native_ids
        subset = [t for t in self._tag_map if t.native_id in set(native_ids)]
        groups = PollScheduler.build_groups(
            subset,
            max_gap=0,
            max_regs=100,
            default_hz=self._config.poll.default_hz if self._config.poll else 1.0,
        )

        self._tasks = []
        for g in groups:
            task = asyncio.create_task(
                self._poll_group(g),
                name=f"poll:{self.source_id}:{g.name}",
            )
            self._tasks.append(task)

        return Subscription(
            id=f"sub:{self.source_id}",
            tag_ids=list(native_ids),
            cancel_event=self._cancel_event,
        )

    async def _poll_group(self, group: PollGroup) -> None:
        period = 1.0 / group.hz if group.hz and group.hz > 0 else 1.0
        while self._cancel_event is not None and not self._cancel_event.is_set():
            try:
                # Читаем всю группу одним запросом (contiguous)
                # Определяем FC по первому native_id
                first = self._tag_by_native.get(group.native_ids[0])
                if first is None:
                    await asyncio.sleep(period)
                    continue
                fc = first.fc or (3 if first.native_id.startswith("40") else 4)
                addr = _parse_address(group.native_ids[0])
                count = sum(
                    2
                    if self._tag_by_native[nid].datatype
                    in ("float32", "int32", "uint32")
                    else 1
                    for nid in group.native_ids
                )
                if fc == 3:
                    regs = await self._client.read_holding(address=addr, count=count)
                else:
                    regs = await self._client.read_input(address=addr, count=count)

                if self._diag:
                    diag_logger.debug(
                        "source=%s group=%s raw=%s",
                        self.source_id,
                        group.name,
                        list(regs),
                    )

                # Раскладываем по тегам (каждый native_id → один register offset)
                offset = 0
                for nid in group.native_ids:
                    entry = self._tag_by_native.get(nid)
                    if entry is None:
                        continue
                    # Для float32/int32 берём 2 регистра, для бит — 1
                    width = 2 if entry.datatype in (
                        "float32", "int32", "uint32"
                    ) else 1
                    chunk = regs[offset : offset + width]
                    offset += width
                    try:
                        value = self._decode(entry, chunk)
                        sample = RawSample(
                            source_id=self.source_id,
                            native_id=nid,
                            raw_value=value,
                            recv_ts=self._recv_ts(),
                            native_quality="good",
                        )
                        if self._on_sample is not None:
                            await self._on_sample(sample)
                    except Exception as e:  # noqa: BLE001
                        bad = RawSample(
                            source_id=self.source_id,
                            native_id=nid,
                            raw_value=None,
                            native_quality=f"modbus.{_modbus_error_kind(e)}",
                            recv_ts=self._recv_ts(),
                        )
                        if self._on_sample is not None:
                            await self._on_sample(bad)
            except (ModbusClientError, ModbusTimeoutError) as e:
                # Вся группа → bad (Modbus PDU атомарен)
                for nid in group.native_ids:
                    bad = RawSample(
                        source_id=self.source_id,
                        native_id=nid,
                        raw_value=None,
                        native_quality=_modbus_error_token(e),
                        recv_ts=self._recv_ts(),
                    )
                    if self._on_sample is not None:
                        await self._on_sample(bad)
            except Exception:  # noqa: BLE001
                logger.exception("poll group %s crashed", group.name)
            await asyncio.sleep(period)

    def _decode(self, entry: TagMapEntry, regs: Sequence[int]) -> float | int | bool | str | None:
        dt = entry.datatype
        extra = getattr(entry, "model_extra", None) or {}
        if dt == "float32":
            wo = extra.get("word_order", "big")
            bo = extra.get("byte_order", "big")
            return decode_float32(regs, word_order=wo, byte_order=bo)
        if dt in ("int16", "uint16", "int32", "uint32"):
            endian = extra.get("endian", "big")
            return decode_int(regs, datatype=dt, endian=endian)
        if dt == "bit":
            # native_id "40200.3"
            _, bit = entry.native_id.split(".")
            return extract_bit(regs[0], int(bit))
        if dt == "boolean":
            return bool(regs[0])
        if dt == "string":
            # Простейшая: байты → ascii (для stub)
            b = bytes([ (r >> 8) & 0xFF for r in regs ] + [ r & 0xFF for r in regs ])
            return b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        # fallback
        return regs[0] if regs else None

    async def _read_registers(self, entry: TagMapEntry) -> list[int]:
        fc = entry.fc or (3 if entry.native_id.startswith("40") else 4)
        addr = _parse_address(entry.native_id)
        count = 2 if entry.datatype in ("float32", "int32", "uint32") else 1
        if fc == 3:
            return list(await self._client.read_holding(address=addr, count=count))
        return list(await self._client.read_input(address=addr, count=count))


def _parse_address(native_id: str) -> int:
    base = native_id.split(".")[0]
    if len(base) >= 3:
        return int(base[2:])
    return int(base)


def _modbus_error_kind(exc: BaseException) -> str:
    """Modbus exception → bare token (без префикса `modbus.`).

    timeout | client_error | exception[.<code>] | client_error
    """
    if isinstance(exc, ModbusTimeoutError):
        return "timeout"
    if isinstance(exc, ModbusClientError):
        return "client_error"
    if isinstance(exc, ModbusException):
        code = getattr(exc, "code", None) or getattr(exc, "exception_code", None)
        return f"exception.{code}" if code else "exception"
    return "client_error"


def _modbus_error_token(exc: BaseException) -> str:
    """Полный токен для native_quality: `modbus.<kind>`."""
    return f"modbus.{_modbus_error_kind(exc)}"
