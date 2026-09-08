"""Shared test fixtures.

Unit tests use ``fakeredis`` and never require Docker.  Tests that need
PostgreSQL / Kafka are marked ``integration`` and skipped unless
``SIEM_RUN_INTEGRATION=1`` (CI sets this with service containers).
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import fakeredis.aioredis
import pytest
from app.schemas.event import SecurityEvent

RUN_INTEGRATION = os.environ.get("SIEM_RUN_INTEGRATION") == "1"

integration = pytest.mark.skipif(
    not RUN_INTEGRATION, reason="integration test — set SIEM_RUN_INTEGRATION=1"
)


@pytest.fixture(autouse=True)
async def _reset_global_pools():
    """pytest-asyncio gives each test its own event loop; the module-level async
    engine / redis pool are bound to whichever loop created them. Dispose after
    every test so the next test rebuilds them on its own loop."""
    yield
    from app.storage.db import dispose_engine
    from app.storage.redis_client import close_redis

    await dispose_engine()
    await close_redis()


@pytest.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        await client.flushall()
        await client.aclose()


@pytest.fixture
def make_event():
    def _make(**overrides) -> SecurityEvent:
        base = {
            "event_id": uuid.uuid4(),
            "timestamp": datetime.now(UTC),
            "source": "ssh-server-01",
            "source_type": "linux_server",
            "event_type": "authentication_failure",
            "source_ip": "203.0.113.10",
            "username": "root",
            "service": "ssh",
            "status": "failure",
            "severity": "medium",
        }
        base.update(overrides)
        return SecurityEvent.from_raw(base)

    return _make
