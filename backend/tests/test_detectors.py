"""Detector unit tests — one Redis-backed engine, synthetic event streams."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.detection.base import DetectorContext
from app.detection.engine import DetectionEngine
from app.detection.rules.brute_force import BruteForceDetector
from app.detection.rules.data_exfiltration import DataExfiltrationDetector
from app.detection.rules.password_spray import PasswordSprayDetector
from app.detection.rules.port_scan import PortScanDetector
from app.detection.rules.privilege_escalation import PrivilegeEscalationDetector
from app.detection.rules.suspicious_sql import SuspiciousSQLDetector
from app.detection.windows import WindowStore
from app.schemas.enums import Severity
from app.schemas.event import SecurityEvent


def ev(**kw) -> SecurityEvent:
    base = {
        "source": "ssh-server-01",
        "source_type": "linux_server",
        "timestamp": datetime.now(UTC),
    }
    base.update(kw)
    return SecurityEvent.from_raw(base)


@pytest.fixture
def ctx_factory(redis_client):
    store = WindowStore(redis_client)

    def _ctx(params):
        return DetectorContext(windows=store, params=params)

    return _ctx


# --------------------------------------------------------------------------- #
async def test_brute_force_fires_after_threshold(ctx_factory):
    det = BruteForceDetector()
    ctx = ctx_factory({"max_failures": 10, "window_seconds": 60})
    t0 = datetime.now(UTC)
    results = []
    for i in range(12):
        e = ev(
            event_type="authentication_failure",
            status="failure",
            source_ip="203.0.113.9",
            username=f"user{i}",
            timestamp=t0 + timedelta(seconds=i),
        )
        results.append(await det.evaluate(e, ctx))
    assert all(r is None for r in results[:9])
    fired = results[10]
    assert fired is not None
    assert fired.rule_id == "RULE-001"
    assert fired.severity == Severity.HIGH
    assert fired.event_count_hint >= 10
    assert 0.5 <= fired.confidence <= 1.0


async def test_brute_force_success_after_spree_is_critical(ctx_factory):
    det = BruteForceDetector()
    ctx = ctx_factory({"max_failures": 5, "window_seconds": 60})
    t0 = datetime.now(UTC)
    for i in range(6):
        await det.evaluate(
            ev(
                event_type="authentication_failure",
                status="failure",
                source_ip="203.0.113.9",
                username="root",
                timestamp=t0 + timedelta(seconds=i),
            ),
            ctx,
        )
    success = ev(
        event_type="authentication_success",
        status="success",
        source_ip="203.0.113.9",
        username="root",
        timestamp=t0 + timedelta(seconds=7),
    )
    fired = await det.evaluate(success, ctx)
    assert fired is not None
    assert fired.severity == Severity.CRITICAL
    assert fired.metadata["account_breached"] is True


async def test_brute_force_below_threshold_silent(ctx_factory):
    det = BruteForceDetector()
    ctx = ctx_factory({"max_failures": 10, "window_seconds": 60})
    for i in range(5):
        r = await det.evaluate(
            ev(
                event_type="authentication_failure",
                status="failure",
                source_ip="203.0.113.1",
                username=f"u{i}",
            ),
            ctx,
        )
    assert r is None


async def test_password_spray(ctx_factory):
    det = PasswordSprayDetector()
    ctx = ctx_factory({"unique_users": 8, "window_seconds": 120})
    fired = None
    for i in range(10):
        fired = await det.evaluate(
            ev(
                event_type="authentication_failure",
                status="failure",
                source_ip="203.0.113.50",
                username=f"acct{i}",
            ),
            ctx,
        )
    assert fired is not None
    assert fired.rule_id == "RULE-002"
    assert fired.metadata["distinct_users"] >= 8


async def test_port_scan(ctx_factory):
    det = PortScanDetector()
    ctx = ctx_factory({"unique_ports": 20, "window_seconds": 30})
    fired = None
    for port in range(1000, 1030):
        fired = await det.evaluate(
            ev(
                event_type="firewall_deny",
                status="denied",
                source_ip="203.0.113.77",
                destination_ip="10.42.1.1",
                destination_port=port,
            ),
            ctx,
        )
    assert fired is not None
    assert fired.rule_id == "RULE-003"
    assert fired.metadata["unique_ports"] >= 20


async def test_privilege_escalation_low_priv_user(ctx_factory):
    det = PrivilegeEscalationDetector()
    ctx = ctx_factory(det.default_params)
    e = ev(
        event_type="privilege_escalation",
        status="success",
        username="bob",
        action="sudo su -",
        source="app-02",
        metadata={"user_role": "user"},
    )
    fired = await det.evaluate(e, ctx)
    assert fired is not None
    assert fired.rule_id == "RULE-004"
    assert fired.severity == Severity.HIGH


async def test_privilege_escalation_admin_daytime_silent(ctx_factory):
    det = PrivilegeEscalationDetector()
    ctx = ctx_factory(det.default_params)
    e = ev(
        event_type="application_event",
        username="alice",
        action="cache.refresh",
        source="app-02",
        metadata={"user_role": "admin"},
        timestamp=datetime.now(UTC).replace(hour=14),
    )
    assert await det.evaluate(e, ctx) is None


@pytest.mark.parametrize(
    "query,should_fire",
    [
        ("SELECT * FROM users WHERE x='' OR 1=1 -- ", True),
        ("SELECT a FROM t UNION SELECT password FROM admins", True),
        ("SELECT load_file('/etc/passwd')", True),
        ("SELECT id, name FROM users WHERE id = $1", False),
    ],
)
async def test_suspicious_sql(ctx_factory, query, should_fire):
    det = SuspiciousSQLDetector()
    ctx = ctx_factory(det.default_params)
    e = ev(event_type="db_query", source="db-01", username="svc_api", metadata={"query": query})
    result = await det.evaluate(e, ctx)
    assert (result is not None) is should_fire


async def test_data_exfiltration(ctx_factory):
    det = DataExfiltrationDetector()
    ctx = ctx_factory({"bytes_threshold": 10_000_000, "window_seconds": 60})
    fired = None
    for _ in range(6):
        fired = await det.evaluate(
            ev(
                event_type="network_flow",
                status="allowed",
                source_ip="10.42.9.9",
                destination_ip="203.0.113.5",
                bytes_out=2_000_000,
            ),
            ctx,
        )
    assert fired is not None
    assert fired.rule_id == "RULE-006"
    assert fired.metadata["window_bytes"] >= 10_000_000


async def test_engine_runs_all_detectors_without_error(redis_client):
    engine = DetectionEngine(redis_client)
    assert len(engine.detectors) == 7
    e = ev(event_type="http_request", status="success", source_ip="10.0.0.5")
    detections = await engine.evaluate(e)
    assert isinstance(detections, list)


async def test_engine_catalogue_shape(redis_client):
    engine = DetectionEngine(redis_client)
    cat = engine.catalogue()
    assert {c["rule_id"] for c in cat} == {f"RULE-00{i}" for i in range(1, 8)}
    for entry in cat:
        assert entry["recommended_action"]
        assert "parameters" in entry
