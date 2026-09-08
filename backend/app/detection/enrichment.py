"""Pluggable enrichment.

The default ``SyntheticEnrichmentProvider`` is fully offline and deterministic:
it derives plausible-looking geo/ASN/reputation attributes from a hash of the IP
so demos are stable.  A real provider would implement the same ``enrich``
coroutine.  No provider requires an API key; external providers must be opt-in.
"""

from __future__ import annotations

import hashlib
import ipaddress
from dataclasses import asdict, dataclass
from typing import Protocol

from app.core.config import settings

_COUNTRIES = ["US", "DE", "NL", "GB", "FR", "SG", "BR", "IN", "RU", "CN", "UA", "SE"]
_CATEGORIES = ["hosting", "residential", "corporate", "tor-exit", "scanner", "vpn"]
_REPUTATIONS = ["clean", "neutral", "suspicious", "malicious"]


@dataclass(slots=True)
class Enrichment:
    ip: str
    is_private: bool
    country: str | None
    asn: str | None
    category: str | None
    reputation: str
    reputation_score: int  # 0 (clean) .. 100 (malicious)
    provider: str

    def as_dict(self) -> dict:
        return asdict(self)


class EnrichmentProvider(Protocol):
    name: str

    async def enrich(self, ip: str) -> Enrichment: ...


# TEST-NET documentation ranges are what the simulator uses to stand in for
# "the internet". Newer Python classifies them as ``is_private``; we treat them
# as external so the Threat Intel view enriches them like real public IPs.
_DOC_NETS = [
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
]


def _is_external(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if any(addr in n for n in _DOC_NETS):
        return True
    return not (addr.is_private or addr.is_loopback or addr.is_link_local)


class SyntheticEnrichmentProvider:
    name = "synthetic"

    async def enrich(self, ip: str) -> Enrichment:
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return Enrichment(ip, False, None, None, None, "neutral", 40, self.name)

        if not _is_external(addr):
            return Enrichment(
                ip=ip,
                is_private=True,
                country=None,
                asn="AS-INTERNAL",
                category="corporate",
                reputation="clean",
                reputation_score=5,
                provider=self.name,
            )

        h = hashlib.sha256(ip.encode()).digest()
        country = _COUNTRIES[h[0] % len(_COUNTRIES)]
        category = _CATEGORIES[h[1] % len(_CATEGORIES)]
        asn_num = 1000 + (int.from_bytes(h[2:4], "big") % 64000)
        score = h[4] % 101
        if category in {"tor-exit", "scanner"}:
            score = max(score, 70)
        reputation = (
            "malicious"
            if score >= 80
            else "suspicious"
            if score >= 55
            else "neutral"
            if score >= 25
            else "clean"
        )
        return Enrichment(
            ip=ip,
            is_private=False,
            country=country,
            asn=f"AS{asn_num}",
            category=category,
            reputation=reputation,
            reputation_score=score,
            provider=self.name,
        )


class NullEnrichmentProvider:
    name = "none"

    async def enrich(self, ip: str) -> Enrichment:
        return Enrichment(ip, False, None, None, None, "neutral", 0, self.name)


def get_enrichment_provider() -> EnrichmentProvider:
    if settings.enrichment_provider == "synthetic":
        return SyntheticEnrichmentProvider()
    return NullEnrichmentProvider()
