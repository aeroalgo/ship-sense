from __future__ import annotations

from pathlib import Path

import pytest

from asyncua import ua
from asyncua.crypto import security_policies as sp

from collector.config.models import SecurityConfig
from collector.domain.errors import ConfigError
from collector.plugins.opcua.security import (  # noqa: E501
    build_client_security,
    ensure_trust_store,
)


def test_build_security_sign_and_encrypt_with_explicit_paths(
    tmp_path: Path,
) -> None:
    """Policy Basic256Sha256 + SignAndEncrypt + явные пути.

    Возвращает args для set_security.
    """
    cert = tmp_path / "client.der"
    key = tmp_path / "client.key"
    cert.write_bytes(b"fake")
    key.write_bytes(b"fake")

    cfg = SecurityConfig(
        policy="Basic256Sha256",
        mode="SignAndEncrypt",
        cert_path=str(cert),
        key_path=str(key),
    )

    args = build_client_security(cfg)

    assert args["policy"] is sp.SecurityPolicyBasic256Sha256
    assert args["mode"] is ua.MessageSecurityMode.SignAndEncrypt
    assert args["certificate"] == str(cert) or args["certificate"] == cert
    assert args["private_key"] == str(key) or args["private_key"] == key


def test_build_security_missing_cert_raises_config_error() -> None:
    """Security required, но cert/key не указаны → явная ConfigError."""
    cfg = SecurityConfig(
        policy="Basic256Sha256",
        mode="SignAndEncrypt",
        cert_path=None,
        key_path=None,
    )

    with pytest.raises(ConfigError, match="requires cert_path and key_path"):
        build_client_security(cfg)


def test_build_security_none_policy_returns_empty() -> None:
    """Policy None или 'None' → пустой dict (безопасность не применяется)."""
    cfg = SecurityConfig(policy="None", mode="None")
    assert build_client_security(cfg) == {}

    cfg2 = SecurityConfig(policy="", mode="")
    assert build_client_security(cfg2) == {}


def test_build_security_sign_mode_maps() -> None:
    """Mode=Sign маппится корректно."""
    cfg = SecurityConfig(
        policy="Basic256Sha256",
        mode="Sign",
        cert_path="c.pem",
        key_path="k.pem",
    )
    args = build_client_security(cfg)
    assert args["mode"] is ua.MessageSecurityMode.Sign


def test_ensure_trust_store_creates_dir(tmp_path: Path) -> None:
    """ensure_trust_store создаёт директорию (idempotent)."""
    target = tmp_path / "trust" / "nested"
    assert not target.exists()

    p = ensure_trust_store(target)
    assert p == target
    assert target.is_dir()

    # повторный вызов не падает
    p2 = ensure_trust_store(target)
    assert p2.is_dir()


def test_build_security_unknown_policy_raises() -> None:
    cfg = SecurityConfig(
        policy="QuantumCrypto3000",
        mode="SignAndEncrypt",
        cert_path="c.pem",
        key_path="k.pem",
    )
    with pytest.raises(ConfigError, match="Unknown.*policy"):
        build_client_security(cfg)
