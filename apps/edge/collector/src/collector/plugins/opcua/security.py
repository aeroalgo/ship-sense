"""OPC UA security helpers.

AC-B3-04: Security: SignAndEncrypt (configurable policy per server).
AC-B3-09: Certificate trust store configurable.
AC-B3-01: Read-only session (no Write service calls).

Инвариант: публичный API НЕ экспортирует write paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from asyncua import ua
from asyncua.crypto import security_policies as sp

from collector.config.models import SecurityConfig
from collector.domain.errors import ConfigError

# Policy name → class mapping (из asyncua.crypto.security_policies)
_POLICY_MAP: dict[str, type] = {
    "Basic256Sha256": sp.SecurityPolicyBasic256Sha256,
    "Aes128Sha256RsaOaep": sp.SecurityPolicyAes128Sha256RsaOaep,
    "Aes256Sha256RsaPss": sp.SecurityPolicyAes256Sha256RsaPss,
    "Basic256": sp.SecurityPolicyBasic256,
    "Basic128Rsa15": sp.SecurityPolicyBasic128Rsa15,
    "None": sp.SecurityPolicyNone,
}

# Mode name → MessageSecurityMode
_MODE_MAP: dict[str, ua.MessageSecurityMode] = {
    "SignAndEncrypt": ua.MessageSecurityMode.SignAndEncrypt,
    "Sign": ua.MessageSecurityMode.Sign,
    "None": ua.MessageSecurityMode.None_,
    "": ua.MessageSecurityMode.None_,
}


def _resolve_policy(name: str) -> type | None:
    if not name or name.lower() in ("none", ""):
        return None
    key = name.strip()
    if key not in _POLICY_MAP:
        raise ConfigError(f"Unknown OPC UA security policy: {name}")
    return _POLICY_MAP[key]


def _resolve_mode(name: str) -> ua.MessageSecurityMode:
    key = (name or "").strip()
    if key not in _MODE_MAP:
        # default to SignAndEncrypt when policy requires security
        return ua.MessageSecurityMode.SignAndEncrypt
    return _MODE_MAP[key]


def build_client_security(config: SecurityConfig) -> dict[str, Any]:
    """
    Построить kwargs для client.set_security(...) по SecurityConfig.

    Возвращает:
      {} — если policy=None / "None" (безопасность не применяется)
      {"policy", "certificate", "private_key", "mode", ...} — для set_security

    Raises:
        ConfigError: если policy требует сертификат, но пути не заданы.
    """
    policy_cls = _resolve_policy(config.policy)
    if policy_cls is None:
        return {}

    mode = _resolve_mode(config.mode)

    # Для None/пустого режима — тоже без set_security
    if mode in (ua.MessageSecurityMode.None_,):
        return {}

    cert_path = config.cert_path
    key_path = config.key_path

    if not cert_path or not key_path:
        raise ConfigError(
            f"OPC UA security requires cert_path and key_path for policy {config.policy}"
        )

    # server_certificate опционален (asyncua сам вытащит при connect)
    kwargs: dict[str, Any] = {
        "policy": policy_cls,
        "certificate": cert_path,
        "private_key": key_path,
        "mode": mode,
    }
    return kwargs


def ensure_trust_store(path: str | Path) -> Path:
    """
    Гарантировать существование директории trust store.

    Используется для хранения доверенных server certs (если требуется offline-валидация).
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
