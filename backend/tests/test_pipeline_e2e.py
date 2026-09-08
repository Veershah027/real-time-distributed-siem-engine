"""End-to-end pipeline: raw events -> validate -> detect -> persist -> alert.

Integration: needs Postgres (uses the real session). Redis is faked.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import fakeredis.aioredis
import pytest
from sqlalchemy import func, select
from tests.conftest import integration

pytestmark = integration


def _raw(**kw) -> dict:
    base = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "ssh-server-01",
        "source_type": "linux_server",
        "event_type": "authentication_failure",
        "status": "failure",
        "severity": "medium",
        "service": "ssh",
    }
    base.update(kw)
    return base


@pytest.fixture
async def prepared_db():
    from app.models import Base
    from app.storage.db import get_engine

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def pipeline():
    from app.streaming.pipeline import Pipeline

    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    p = Pipeline(r)
    yield p
    await r.aclose()


async def test_events_are_persisted(pipeline, prepared_db):
    from app.models import SecurityEventRow
    from app.storage.db import session_scope

    batch = [_raw(event_type="http_request", status="success", severity="info") for _ in range(20)]
    await pipeline.process_batch(batch)

    async with session_scope() as s:
        count = await s.scalar(select(func.count()).select_from(SecurityEventRow))
    assert count == 20


async def test_duplicate_events_deduped(pipeline, prepared_db):
    from app.models import SecurityEventRow
    from app.storage.db import session_scope

    ev = _raw()
    await pipeline.process_batch([ev, ev, ev])
    async with session_scope() as s:
        count = await s.scalar(select(func.count()).select_from(SecurityEventRow))
    assert count == 1


async def test_brute_force_creates_single_correlated_alert(pipeline, prepared_db):
    from app.models import Alert
    from app.storage.db import session_scope

    t0 = datetime.now(UTC)
    batch = [
        _raw(
            source_ip="203.0.113.66",
            username=f"user{i}",
            timestamp=(t0 + timedelta(seconds=i)).isoformat(),
        )
        for i in range(18)
    ]
    await pipeline.process_batch(batch)

    async with session_scope() as s:
        alerts = list((await s.scalars(select(Alert).where(Alert.rule_id == "RULE-001"))).all())
    assert len(alerts) == 1
    assert alerts[0].event_count >= 10
    assert alerts[0].severity in ("high", "critical")
    assert alerts[0].source_ip == "203.0.113.66"
    assert len(alerts[0].evidence) >= 1


async def test_malformed_events_do_not_break_batch(pipeline, prepared_db):
    from app.models import SecurityEventRow
    from app.storage.db import session_scope

    batch = [
        _raw(event_type="http_request"),
        {"garbage": True, "timestamp": "not-a-date", "event_id": "x"},
        _raw(event_type="http_request"),
    ]
    await pipeline.process_batch(batch)
    async with session_scope() as s:
        count = await s.scalar(select(func.count()).select_from(SecurityEventRow))
    assert count >= 2
