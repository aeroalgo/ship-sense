from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from apps.edge.gateway.proof.generator import build_proof


def test_build_proof_hashes_config_and_includes_reject_samples(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("mode: modbus\nlisten_port: 5020\n", encoding="utf-8")
    log_path = tmp_path / "rejected_writes.log"
    log_path.write_text(
        json.dumps(
            {
                "ts": "2026-07-31T12:00:00+00:00",
                "function_code": 16,
                "source_ip": "10.0.0.4",
                "raw_pdu_hash": "abc123",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_proof(config_path, log_path)

    assert result["config_sha256"] == hashlib.sha256(config_path.read_bytes()).hexdigest()
    assert result["generated_at"]
    pdf_path = Path(result["pdf_path"])
    assert pdf_path.exists()
    pdf = pdf_path.read_bytes()
    assert pdf.startswith(b"%PDF-")
    assert b"10.0.0.4" in pdf
    assert b"function_code=16" in pdf


def test_build_proof_missing_log_fails_explicitly(tmp_path: Path) -> None:
    config_path = tmp_path / "gateway.yaml"
    config_path.write_text("mode: modbus\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="proof log"):
        build_proof(config_path, tmp_path / "missing.log")
