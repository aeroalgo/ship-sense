from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_PAGE_WIDTH = 612
_PAGE_HEIGHT = 792
_MARGIN = 54
_LINE_HEIGHT = 14


def build_proof(config_path: Path, log_path: Path) -> dict[str, Any]:
    """Build a self-contained PDF proof from gateway config and reject logs."""
    config_path = Path(config_path)
    log_path = Path(log_path)
    if not config_path.is_file():
        raise FileNotFoundError(f"proof config: {config_path}")
    if not log_path.is_file():
        raise FileNotFoundError(f"proof log: {log_path}")

    config_sha256 = hashlib.sha256(config_path.read_bytes()).hexdigest()
    samples = _read_log_samples(log_path)
    generated_at = datetime.now(UTC).isoformat()
    lines = [
        "ShipSense I1 read-only gateway proof",
        f"generated_at={generated_at}",
        f"config_sha256={config_sha256}",
        f"reject_samples={len(samples)}",
        "",
    ]
    lines.extend(_sample_line(sample) for sample in samples)

    pdf_path = log_path.with_name("gateway-proof.pdf")
    pdf_path.write_bytes(_render_pdf(lines))
    return {
        "pdf_path": str(pdf_path),
        "config_sha256": config_sha256,
        "generated_at": generated_at,
    }


def _read_log_samples(log_path: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for line_number, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid proof log JSON at line {line_number}") from error
        if not isinstance(record, dict):
            raise ValueError(f"proof log record at line {line_number} is not an object")
        samples.append(record)
    return samples


def _sample_line(sample: dict[str, Any]) -> str:
    return " ".join(
        f"{key}={sample[key]}"
        for key in ("ts", "function_code", "source_ip", "raw_pdu_hash")
        if key in sample
    )


def _render_pdf(lines: list[str]) -> bytes:
    escaped_lines = [_pdf_escape(line) for line in lines]
    content_lines = [
        "BT",
        "/F1 10 Tf",
        f"{_MARGIN} {_PAGE_HEIGHT - _MARGIN} Td",
    ]
    for index, line in enumerate(escaped_lines):
        if index:
            content_lines.append(f"0 -{_LINE_HEIGHT} Td")
        content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(pdf)


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
