"""Alert correlation logic — exercised with an in-memory fake repository."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.detection.base import Detection
from app.detection.correlation import AlertCorrelator
from app.models import Alert
from app.schemas.enums import AlertStatus, DetectionKind, Severity


class FakeAlertRepo:
    def __init__(self):
        self.alerts: list[Alert] = []

    async def get_open_by_key(self, rule_id, correlation_key):
        for a in self.alerts:
            if (
                a.rule_id == rule_id
                and a.correlation_key == correlation_key
                and a.status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)
            ):
                return a
        return None

    async def add(self, alert):
        self.alerts.append(alert)
        return alert


def det(**kw) -> Detection:
    base = {
        "rule_id": "RULE-001",
        "kind": DetectionKind.RULE,
        "title": "Brute force",
        "description": "d",
        "severity": Severity.HIGH,
        "confidence": 0.7,
        "correlation_key": "srcip:203.0.113.9",
        "source_ip": "203.0.113.9",
        "affected_host": "ssh-server-01",
        "recommended_action": "block",
        "evidence": [
            {"event_id": "e1", "timestamp": datetime.now(UTC).isoformat(), "summary": "x"}
        ],
        "involved_users": ["root"],
        "involved_hosts": ["ssh-server-01"],
        "event_count_hint": 11,
        "triggered_at": datetime.now(UTC),
    }
    base.update(kw)
    return Detection(**base)


@pytest.fixture
def correlator():
    return AlertCorrelator(FakeAlertRepo())


async def test_first_detection_creates_alert(correlator):
    alert, created = await correlator.apply(det())
    assert created is True
    assert alert.event_count == 11
    assert alert.status == AlertStatus.OPEN


async def test_same_key_folds_into_one_alert(correlator):
    a1, c1 = await correlator.apply(det(event_count_hint=11))
    a2, c2 = await correlator.apply(
        det(
            event_count_hint=1,
            confidence=0.9,
            evidence=[{"event_id": "e2", "timestamp": "t", "summary": "y"}],
        )
    )
    assert c1 is True and c2 is False
    assert a1 is a2
    assert a2.event_count == 12
    assert a2.confidence == 0.9
    assert len(a2.evidence) == 2


async def test_severity_escalates_but_never_downgrades(correlator):
    a, _ = await correlator.apply(det(severity=Severity.HIGH))
    a, _ = await correlator.apply(det(severity=Severity.CRITICAL, title="worse"))
    assert a.severity == Severity.CRITICAL
    a, _ = await correlator.apply(det(severity=Severity.MEDIUM))
    assert a.severity == Severity.CRITICAL


async def test_different_key_creates_separate_alert(correlator):
    await correlator.apply(det(correlation_key="srcip:1.1.1.1"))
    _, created = await correlator.apply(det(correlation_key="srcip:2.2.2.2"))
    assert created is True
    assert len(correlator.repo.alerts) == 2


async def test_evidence_is_capped(correlator):
    for i in range(40):
        await correlator.apply(
            det(evidence=[{"event_id": f"e{i}", "timestamp": "t", "summary": f"s{i}"}])
        )
    assert len(correlator.repo.alerts[0].evidence) <= 25
