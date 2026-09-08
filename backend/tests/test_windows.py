"""Sliding-window primitives (fakeredis)."""

from __future__ import annotations

import time

import pytest
from app.detection.windows import WindowStore


@pytest.fixture
def store(redis_client):
    return WindowStore(redis_client)


async def test_add_and_measure_counts_and_uniques(store):
    now = time.time()
    for i in range(5):
        res = await store.add_and_measure(
            "t", "1.2.3.4", f"user{i % 2}", window_seconds=60, now=now + i
        )
    assert res.count == 5
    assert res.unique_values == {"user0", "user1"}
    assert res.span_seconds == pytest.approx(4, abs=0.5)


async def test_window_expiry_trims_old_entries(store):
    now = time.time()
    await store.add_and_measure("t", "e", "a", window_seconds=10, now=now - 100)
    res = await store.add_and_measure("t", "e", "b", window_seconds=10, now=now)
    assert res.count == 1
    assert res.unique_values == {"b"}


async def test_incr_sum_accumulates(store):
    now = time.time()
    total = 0
    for i in range(4):
        total = await store.incr_sum("bytes", "flow", 1000, window_seconds=60, now=now + i)
    assert total == 4000


async def test_measure_without_adding(store):
    now = time.time()
    await store.add_and_measure("t", "e", "x", window_seconds=60, now=now)
    res = await store.measure("t", "e", window_seconds=60)
    assert res.count == 1
