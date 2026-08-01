from apps.edge.ota.gate import AnchorageDecision, can_update


def test_update_requires_anchorage_and_no_override_failures() -> None:
    assert can_update(anchored=True, override=False) == AnchorageDecision.ALLOWED
    assert can_update(anchored=False, override=False) == AnchorageDecision.BLOCKED
    assert can_update(anchored=False, override=True) == AnchorageDecision.ALLOWED


def test_update_fails_closed_for_unknown_anchorage() -> None:
    assert can_update(anchored=None, override=False) == AnchorageDecision.BLOCKED
