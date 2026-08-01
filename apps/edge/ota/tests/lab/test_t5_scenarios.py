from __future__ import annotations

import hashlib
from dataclasses import dataclass

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from apps.edge.ota.rollback import Slot, rollback_after_failed_health, resume_offset
from apps.edge.ota.verify import SignatureVerificationError, verify_bundle


@dataclass
class LabOtaDriver:
    """Deterministic CI stand-in for the RAUC/collector lab hooks."""

    active_slot: Slot = Slot.A
    pending_slot: Slot | None = None
    collector_alive: bool = True
    image_healthy: bool = True
    downloaded_bytes: int = 0
    installed_payload: bytes = b""

    def stage(self, payload: bytes, signature: bytes, public_key: bytes) -> None:
        verify_bundle(payload, signature, public_key)
        self.pending_slot = Slot.B if self.active_slot is Slot.A else Slot.A
        self.installed_payload = payload

    def switch_and_healthcheck(self) -> None:
        if self.pending_slot is None:
            return
        healthy = self.collector_alive and self.image_healthy
        decision = rollback_after_failed_health(
            active_slot=self.active_slot,
            pending_slot=self.pending_slot if not healthy else None,
        )
        if decision.should_rollback:
            self.pending_slot = None
            return
        self.active_slot = self.pending_slot
        self.pending_slot = None

    def download_with_interrupts(self, payload: bytes, *, chunk_size: int, cuts: int) -> bytes:
        for _ in range(cuts):
            self.downloaded_bytes = min(len(payload), self.downloaded_bytes + chunk_size + 1)
            self.downloaded_bytes = resume_offset(
                downloaded_bytes=self.downloaded_bytes,
                chunk_size=chunk_size,
            )
        self.downloaded_bytes = len(payload)
        return payload


def _signed_bundle(payload: bytes = b"ship-sense ota image") -> tuple[bytes, bytes, bytes]:
    private_key = Ed25519PrivateKey.generate()
    return payload, private_key.sign(payload), private_key.public_key().public_bytes_raw()


def test_broken_image_rolls_back_to_active_slot() -> None:
    driver = LabOtaDriver(image_healthy=False)
    payload, signature, public_key = _signed_bundle()

    driver.stage(payload, signature, public_key)
    driver.switch_and_healthcheck()

    assert driver.active_slot is Slot.A
    assert driver.pending_slot is None


def test_dead_collector_after_healthy_boot_rolls_back() -> None:
    driver = LabOtaDriver(collector_alive=False)
    payload, signature, public_key = _signed_bundle()

    driver.stage(payload, signature, public_key)
    driver.switch_and_healthcheck()

    assert driver.active_slot is Slot.A
    assert driver.pending_slot is None


def test_unsigned_bundle_is_rejected_before_staging() -> None:
    driver = LabOtaDriver()
    payload, _, public_key = _signed_bundle()

    with pytest.raises(SignatureVerificationError):
        driver.stage(payload, b"", public_key)

    assert driver.pending_slot is None
    assert driver.installed_payload == b""


def test_ten_interrupted_downloads_resume_and_verify_hash() -> None:
    driver = LabOtaDriver()
    payload = b"ota-image" * 257

    downloaded = driver.download_with_interrupts(payload, chunk_size=128, cuts=10)

    assert downloaded == payload
    assert driver.downloaded_bytes == len(payload)
    assert hashlib.sha256(downloaded).hexdigest() == hashlib.sha256(payload).hexdigest()
