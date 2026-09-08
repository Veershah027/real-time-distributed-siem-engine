"""Synthetic enrichment provider."""

from __future__ import annotations

import pytest
from app.detection.enrichment import SyntheticEnrichmentProvider


@pytest.fixture
def provider():
    return SyntheticEnrichmentProvider()


async def test_private_ip_is_internal(provider):
    e = await provider.enrich("10.42.1.5")
    assert e.is_private is True
    assert e.reputation == "clean"
    assert e.asn == "AS-INTERNAL"


async def test_public_ip_is_deterministic(provider):
    a = await provider.enrich("203.0.113.10")
    b = await provider.enrich("203.0.113.10")
    assert a.as_dict() == b.as_dict()
    assert a.country is not None
    assert 0 <= a.reputation_score <= 100


async def test_invalid_ip_graceful(provider):
    e = await provider.enrich("not-an-ip")
    assert e.reputation == "neutral"


async def test_reputation_scales_with_score(provider):
    for i in range(50):
        e = await provider.enrich(f"198.51.100.{i}")
        if e.reputation_score >= 80:
            assert e.reputation == "malicious"
        elif e.reputation_score < 25:
            assert e.reputation == "clean"
