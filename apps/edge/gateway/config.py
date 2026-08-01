from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class GatewaySettings(BaseModel):
    mode: Literal["modbus", "opcua", "both"] = "modbus"
    listen_host: str = "0.0.0.0"
    listen_port: int = Field(default=5020, ge=1, le=65535)
    upstream_host: str = "emulator"
    upstream_port: int = Field(default=5020, ge=1, le=65535)
    log_path: Path = Path("/var/log/shipsense/rejected_writes.log")

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        values: dict[str, object] = {}
        for field, env_name in {
            "mode": "SHIPSSENSE_GATEWAY_MODE",
            "listen_host": "SHIPSSENSE_GATEWAY_LISTEN_HOST",
            "listen_port": "SHIPSSENSE_GATEWAY_LISTEN_PORT",
            "upstream_host": "SHIPSSENSE_GATEWAY_UPSTREAM_HOST",
            "upstream_port": "SHIPSSENSE_GATEWAY_UPSTREAM_PORT",
            "log_path": "SHIPSSENSE_GATEWAY_LOG_PATH",
        }.items():
            if (value := os.getenv(env_name)) is not None:
                values[field] = value
        return cls.model_validate(values)
