from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawSample(BaseModel):
    source_id: str = Field(..., description="ID из sources.yaml, напр. aps_main")
    native_id: str = Field(..., description="Адрес протокола: '40101' или 'ns=2;s=...'")
    raw_value: Any = Field(..., description="Декодированное значение до unit conversion")
    native_quality: str | None = Field(
        None, description="Сырой код: Modbus exception, OPC StatusCode name"
    )
    recv_ts: datetime = Field(..., description="UTC момент получения на edge (aware)")
    source_ts: datetime | None = Field(
        None, description="Timestamp от источника если протокол отдал"
    )
    sequence: int | None = Field(None, description="OPC UA sequence для dedup")


class RawTagDescriptor(BaseModel):
    native_id: str
    name: str | None = None
    unit: str | None = None
    datatype: str | None = None
    description: str | None = None
