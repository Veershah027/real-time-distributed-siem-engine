"""Security-focused tests: malformed input, oversized payloads, injection-like
strings, and unauthorized operations.
"""

from __future__ import annotations

import pytest
from app.schemas.event import SecurityEvent

integration = pytest.mark.integration


class TestInputHardening:
    def test_sql_injection_string_in_username_is_not_executed_just_stored(self):
        ev = SecurityEvent.from_raw({"source": "x", "username": "admin'; DROP TABLE users; --"})
        # stored as an opaque, length-bounded string; no evaluation
        assert ev.username.startswith("admin'; DROP TABLE")

    def test_oversized_message_truncated(self):
        ev = SecurityEvent.from_raw({"source": "x", "message": "x" * 1_000_000})
        assert len(ev.message) <= 2048

    def test_deeply_nested_metadata_bounded(self):
        payload = {"source": "x", "metadata": {f"k{i}": {"a": {"b": i}} for i in range(500)}}
        ev = SecurityEvent.from_raw(payload)
        assert len(ev.metadata) <= 50

    def test_null_bytes_and_control_chars_survive_without_crash(self):
        ev = SecurityEvent.from_raw({"source": "x\x00y", "message": "line1\nline2\x07"})
        assert isinstance(ev.source, str)

    @pytest.mark.parametrize(
        "bad", [{"timestamp": "not-a-date"}, {"timestamp": []}, {"timestamp": {}}]
    )
    def test_unparseable_timestamp_raises_cleanly(self, bad):
        # from_raw normalizes; a bare SecurityEvent with junk timestamp raises ValueError
        with pytest.raises(Exception):
            SecurityEvent(source="x", **bad)  # type: ignore[arg-type]


@integration
class TestApiHardening:
    @pytest.fixture(autouse=True)
    async def _client(self):
        from app.main import create_app
        from app.models import Base
        from app.storage.db import get_engine
        from httpx import ASGITransport, AsyncClient

        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            self.client = c
            yield

    async def test_malformed_json_body_rejected(self):
        r = await self.client.patch(
            "/api/alerts/00000000-0000-0000-0000-000000000000",
            content="{not json",
            headers={"content-type": "application/json"},
        )
        assert r.status_code in (400, 422)

    async def test_invalid_uuid_path_rejected(self):
        r = await self.client.get("/api/events/not-a-uuid")
        assert r.status_code == 422

    async def test_unknown_alert_status_rejected(self):
        r = await self.client.patch(
            "/api/alerts/00000000-0000-0000-0000-000000000000",
            json={"status": "pwned"},
        )
        assert r.status_code == 422

    async def test_error_response_shape_is_consistent(self):
        r = await self.client.get("/api/events/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
        assert "detail" in r.json()

    async def test_security_headers_present(self):
        r = await self.client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert "x-request-id" in r.headers
