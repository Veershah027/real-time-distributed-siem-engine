"""API tests — require Postgres + Redis (integration).

CI provides both as service containers and sets SIEM_RUN_INTEGRATION=1.
Locally:  docker compose up -d postgres redis  &&  SIEM_RUN_INTEGRATION=1 pytest -k api
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

integration = pytest.mark.integration

pytestmark = integration


@pytest.fixture
async def app_client():
    from app.main import create_app
    from app.models import Base
    from app.storage.db import get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # trigger lifespan-equivalent setup
        from app.storage.redis_client import get_redis

        await get_redis().flushall()
        yield client


@pytest.fixture
async def seed_event(app_client):
    from app.schemas.event import SecurityEvent
    from app.storage.db import session_scope
    from app.storage.repositories import EventRepository

    ev = SecurityEvent.from_raw(
        {
            "event_id": str(uuid.uuid4()),
            "source": "ssh-server-01",
            "source_type": "linux_server",
            "event_type": "authentication_failure",
            "source_ip": "203.0.113.42",
            "username": "root",
            "severity": "medium",
            "status": "failure",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    async with session_scope() as s:
        await EventRepository(s).bulk_insert([ev])
    return ev


async def test_health(app_client):
    r = await app_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_ready_reports_components(app_client):
    r = await app_client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "postgres" in body["checks"] and "redis" in body["checks"]


async def test_list_events_pagination(app_client, seed_event):
    r = await app_client.get("/api/events?limit=10&offset=0")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 10
    assert body["total"] >= 1
    assert isinstance(body["items"], list)


async def test_get_event_by_id(app_client, seed_event):
    r = await app_client.get(f"/api/events/{seed_event.event_id}")
    assert r.status_code == 200
    assert r.json()["source_ip"] == "203.0.113.42"


async def test_get_missing_event_404(app_client):
    r = await app_client.get(f"/api/events/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_events_limit_is_capped(app_client):
    r = await app_client.get("/api/events?limit=9999")
    assert r.status_code == 422


async def test_metrics_shape(app_client):
    r = await app_client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    for key in ("events_per_second", "active_alerts_total", "detection_rate"):
        assert key in body


async def test_detections_catalogue(app_client):
    r = await app_client.get("/api/detections")
    assert r.status_code == 200
    ids = {x["rule_id"] for x in r.json()["rules"]}
    assert "RULE-001" in ids


async def test_system_status(app_client):
    r = await app_client.get("/api/system/status")
    assert r.status_code == 200
    assert "components" in r.json()


async def test_prometheus_exposition(app_client):
    r = await app_client.get("/metrics")
    assert r.status_code == 200
    assert "siem_events_ingested_total" in r.text


async def test_alert_lifecycle(app_client):
    """Create an alert directly, then drive it through the triage API."""
    from app.detection.base import Detection
    from app.detection.correlation import AlertCorrelator
    from app.schemas.enums import DetectionKind, Severity
    from app.storage.db import session_scope
    from app.storage.repositories import AlertRepository

    detn = Detection(
        rule_id="RULE-001",
        kind=DetectionKind.RULE,
        title="brute force test",
        description="d",
        severity=Severity.HIGH,
        confidence=0.9,
        correlation_key=f"test:{uuid.uuid4()}",
        source_ip="203.0.113.9",
        affected_host="ssh-server-01",
        recommended_action="block",
        event_count_hint=11,
        triggered_at=datetime.now(UTC),
    )
    async with session_scope() as s:
        alert, _ = await AlertCorrelator(AlertRepository(s)).apply(detn)
        await s.flush()
        alert_id = str(alert.alert_id)

    r = await app_client.get(f"/api/alerts/{alert_id}")
    assert r.status_code == 200
    assert r.json()["event_count"] == 11

    r = await app_client.patch(f"/api/alerts/{alert_id}", json={"status": "acknowledged"})
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"

    # invalid transition acknowledged -> false_positive is allowed; resolved -> acknowledged is not
    r = await app_client.patch(f"/api/alerts/{alert_id}", json={"status": "resolved"})
    assert r.status_code == 200
    r = await app_client.patch(f"/api/alerts/{alert_id}", json={"status": "acknowledged"})
    assert r.status_code == 409


async def test_simulator_control_roundtrip(app_client):
    r = await app_client.post("/api/simulator/start", json={"rate": 25, "scenario": "port_scan"})
    assert r.status_code == 200
    r = await app_client.get("/api/simulator/status")
    assert r.json()["desired"]["scenario"] == "port_scan"
    r = await app_client.post("/api/simulator/stop")
    assert r.json()["desired"]["running"] is False


async def test_simulator_rejects_unknown_scenario(app_client):
    r = await app_client.post("/api/simulator/start", json={"scenario": "nuke"})
    assert r.status_code == 422
