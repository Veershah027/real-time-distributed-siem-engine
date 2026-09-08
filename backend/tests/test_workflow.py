"""Incident-workflow state machine (no infra)."""

from __future__ import annotations

import pytest
from app.schemas.enums import AlertStatus
from app.services.alerts import _ALLOWED_TRANSITIONS


@pytest.mark.parametrize(
    "status,active",
    [
        (AlertStatus.OPEN, True),
        (AlertStatus.ACKNOWLEDGED, True),
        (AlertStatus.INVESTIGATING, True),
        (AlertStatus.RESOLVED, False),
        (AlertStatus.FALSE_POSITIVE, False),
    ],
)
def test_is_active(status, active):
    assert status.is_active is active


def test_forward_workflow_is_allowed():
    assert AlertStatus.ACKNOWLEDGED in _ALLOWED_TRANSITIONS[AlertStatus.OPEN]
    assert AlertStatus.INVESTIGATING in _ALLOWED_TRANSITIONS[AlertStatus.ACKNOWLEDGED]
    assert AlertStatus.RESOLVED in _ALLOWED_TRANSITIONS[AlertStatus.INVESTIGATING]


def test_false_positive_reachable_from_every_active_state():
    for s in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING):
        assert AlertStatus.FALSE_POSITIVE in _ALLOWED_TRANSITIONS[s]


def test_terminal_states_only_reopen():
    assert _ALLOWED_TRANSITIONS[AlertStatus.RESOLVED] == {AlertStatus.OPEN}
    assert _ALLOWED_TRANSITIONS[AlertStatus.FALSE_POSITIVE] == {AlertStatus.OPEN}


def test_cannot_skip_backwards_from_resolved_to_investigating():
    assert AlertStatus.INVESTIGATING not in _ALLOWED_TRANSITIONS[AlertStatus.RESOLVED]
