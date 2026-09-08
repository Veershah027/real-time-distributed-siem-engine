"""Event validation + normalization."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.schemas.enums import EventStatus, EventType, Severity, SourceType
from app.schemas.event import RawEvent, SecurityEvent


def test_from_raw_minimal_defaults():
    ev = SecurityEvent.from_raw({"source": "web-01"})
    assert isinstance(ev.event_id, uuid.UUID)
    assert ev.event_type == EventType.UNKNOWN
    assert ev.severity == Severity.INFO
    assert ev.timestamp.tzinfo is not None


def test_timestamp_normalized_to_utc():
    ev = SecurityEvent.from_raw({"source": "x", "timestamp": "2026-09-07T12:00:00+02:00"})
    assert ev.timestamp.utcoffset() == timedelta(0)
    assert ev.timestamp.hour == 10


def test_timestamp_z_suffix_and_epoch():
    a = SecurityEvent.from_raw({"source": "x", "timestamp": "2026-09-07T12:00:00Z"})
    b = SecurityEvent.from_raw({"source": "x", "timestamp": 1_757_246_400})
    assert a.timestamp.tzinfo is UTC or a.timestamp.utcoffset() == timedelta(0)
    assert b.timestamp.year == 2025 or b.timestamp.year == 2026


def test_far_future_timestamp_clamped():
    future = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    ev = SecurityEvent.from_raw({"source": "x", "timestamp": future})
    assert ev.timestamp <= datetime.now(UTC) + timedelta(minutes=1)


@pytest.mark.parametrize(
    "raw_ip,expected",
    [("10.0.0.1", "10.0.0.1"), ("not-an-ip", None), ("", None), ("999.1.1.1", None)],
)
def test_ip_validation(raw_ip, expected):
    ev = SecurityEvent.from_raw({"source": "x", "source_ip": raw_ip})
    assert ev.source_ip == expected


@pytest.mark.parametrize("port,expected", [(22, 22), ("443", 443), (99999, None), ("x", None)])
def test_port_validation(port, expected):
    ev = SecurityEvent.from_raw({"source": "x", "destination_port": port})
    assert ev.destination_port == expected


def test_unknown_enums_funnel_to_unknown():
    ev = SecurityEvent.from_raw(
        {"source": "x", "event_type": "wat", "source_type": "toaster", "status": "??"}
    )
    assert ev.event_type == EventType.UNKNOWN
    assert ev.source_type == SourceType.UNKNOWN
    assert ev.status == EventStatus.INFO


def test_malformed_metadata_is_bounded():
    ev = SecurityEvent.from_raw({"source": "x", "metadata": "notadict"})
    assert ev.metadata == {}
    big = {f"k{i}": i for i in range(200)}
    ev2 = SecurityEvent.from_raw({"source": "x", "metadata": big})
    assert len(ev2.metadata) <= 50


def test_extra_fields_captured_into_metadata():
    ev = SecurityEvent.from_raw({"source": "x", "weird_field": "kept"})
    assert ev.metadata.get("weird_field") == "kept"


def test_message_length_bounded():
    ev = SecurityEvent.from_raw({"source": "x", "message": "A" * 9000})
    assert ev.message is not None and len(ev.message) <= 2048


def test_bytes_coerced_and_clamped():
    ev = SecurityEvent.from_raw({"source": "x", "bytes_out": "-5", "bytes_in": "abc"})
    assert ev.bytes_out == 0
    assert ev.bytes_in == 0


def test_event_is_frozen(make_event):
    ev = make_event()
    with pytest.raises(Exception):
        ev.severity = Severity.CRITICAL  # type: ignore[misc]


def test_raw_event_allows_extra():
    r = RawEvent(source="x", foo="bar")  # type: ignore[call-arg]
    assert r.model_dump().get("foo") == "bar"


def test_severity_rank_ordering():
    assert Severity.CRITICAL.rank > Severity.HIGH.rank > Severity.MEDIUM.rank
