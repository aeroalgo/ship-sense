from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from apps.edge.ota.verify import SignatureVerificationError, verify_bundle


def test_verify_bundle_rejects_unsigned_or_tampered_payload() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()
    payload = b"ship-sense ota image"
    signature = private_key.sign(payload)

    assert verify_bundle(payload, signature, public_key) is True

    with pytest.raises(SignatureVerificationError):
        verify_bundle(payload + b"-tampered", signature, public_key)

    with pytest.raises(SignatureVerificationError):
        verify_bundle(payload, b"", public_key)
