"""Redis-backed sliding-window primitives used by rule detectors.

Each window is a Redis sorted set keyed by ``siem:win:<name>:<entity>`` whose
score is the event's epoch-seconds timestamp and whose member is a unique token
(``<ts>:<value>``).  ``add_and_measure`` trims expired members, adds the new one,
sets a TTL, and returns the current window contents in one round trip via a
pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import redis.asyncio as redis


@dataclass(slots=True)
class WindowResult:
    count: int
    unique_values: set[str]
    oldest_ts: float
    newest_ts: float

    @property
    def span_seconds(self) -> float:
        return max(0.0, self.newest_ts - self.oldest_ts)


class WindowStore:
    def __init__(self, client: redis.Redis, *, namespace: str = "siem:win") -> None:
        self._r = client
        self._ns = namespace

    def _key(self, name: str, entity: str) -> str:
        return f"{self._ns}:{name}:{entity}"

    async def add_and_measure(
        self,
        name: str,
        entity: str,
        value: str,
        *,
        window_seconds: int,
        now: float | None = None,
    ) -> WindowResult:
        now = now if now is not None else time.time()
        cutoff = now - window_seconds
        key = self._key(name, entity)
        member = f"{now:.4f}:{value}"

        pipe = self._r.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zadd(key, {member: now})
        pipe.expire(key, window_seconds + 30)
        pipe.zrange(key, 0, -1, withscores=True)
        results = await pipe.execute()

        entries: list[tuple[str, float]] = results[3]
        values: set[str] = set()
        scores: list[float] = []
        for m, score in entries:
            scores.append(score)
            # member format "<ts>:<value>" — value may itself contain ':'
            _, _, v = m.partition(":")
            values.add(v)
        if not scores:  # pragma: no cover - always has the just-added member
            return WindowResult(0, set(), now, now)
        return WindowResult(
            count=len(scores),
            unique_values=values,
            oldest_ts=min(scores),
            newest_ts=max(scores),
        )

    async def measure(self, name: str, entity: str, *, window_seconds: int) -> WindowResult:
        now = time.time()
        cutoff = now - window_seconds
        key = self._key(name, entity)
        pipe = self._r.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zrange(key, 0, -1, withscores=True)
        _, entries = await pipe.execute()
        if not entries:
            return WindowResult(0, set(), now, now)
        values = {m.partition(":")[2] for m, _ in entries}
        scores = [s for _, s in entries]
        return WindowResult(len(scores), values, min(scores), max(scores))

    async def incr_sum(
        self, name: str, entity: str, amount: int, *, window_seconds: int, now: float | None = None
    ) -> int:
        """Sliding-window numeric sum (e.g. outbound bytes). Returns window total."""
        now = now if now is not None else time.time()
        cutoff = now - window_seconds
        key = self._key(name, entity)
        member = f"{now:.4f}:{amount}"
        pipe = self._r.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zadd(key, {member: now})
        pipe.expire(key, window_seconds + 30)
        pipe.zrange(key, 0, -1)
        results = await pipe.execute()
        total = 0
        for m in results[3]:
            try:
                total += int(m.partition(":")[2])
            except ValueError:  # pragma: no cover
                continue
        return total
