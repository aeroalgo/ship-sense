from __future__ import annotations


def parse_writer_endpoint(value: str) -> tuple[str, int]:
    """Parse a TCP ``host:port`` endpoint from environment/config."""
    host, separator, port_text = value.rpartition(":")
    if not separator or not host or not port_text:
        raise ValueError(f"writer endpoint must be host:port, got {value!r}")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ValueError(f"writer endpoint port must be an integer: {value!r}") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"writer endpoint port out of range: {port}")
    return host, port


def parse_modbus_endpoint(value: str) -> tuple[str, int]:
    return parse_writer_endpoint(value)
