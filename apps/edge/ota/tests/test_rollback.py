import pytest

from apps.edge.ota.rollback import Slot, rollback_after_failed_health, resume_offset


def test_failed_health_rolls_back_pending_slot() -> None:
    decision = rollback_after_failed_health(active_slot=Slot.A, pending_slot=Slot.B)

    assert decision.target_slot is Slot.A
    assert decision.should_rollback is True


def test_resume_offset_aligns_to_completed_chunk() -> None:
    assert resume_offset(downloaded_bytes=257, chunk_size=128) == 256

    with pytest.raises(ValueError):
        resume_offset(downloaded_bytes=-1, chunk_size=128)
