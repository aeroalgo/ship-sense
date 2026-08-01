from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class SignatureVerificationError(ValueError):
    """Bundle signature is invalid or cannot be checked."""


def verify_bundle(payload: bytes, signature: bytes, public_key: bytes) -> bool:
    if not payload or not signature or not public_key:
        raise SignatureVerificationError("bundle signature inputs are required")
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, payload)
    except (InvalidSignature, ValueError) as exc:
        raise SignatureVerificationError("bundle signature verification failed") from exc
    return True
