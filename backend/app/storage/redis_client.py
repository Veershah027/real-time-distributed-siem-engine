"""Redis connection helpers + pub/sub channel names.

Redis holds only short-lived real-time state:
  * sliding-window sets for detectors        (TTL = rule window + slack)
  * rolling metric counters for the dashboard (TTL ~ 5 min)
  * a de-dupe set of recently seen event ids  (TTL ~ 10 min)
  * pub/sub fan-out of events & alerts to WebSocket clients
PostgreSQL remains the source of truth.
"""

from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings

CHANNEL_EVENTS = "siem:stream:events"
CHANNEL_ALERTS = "siem:stream:alerts"
CHANNEL_METRICS = "siem:stream:metrics"

_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            socket_keepalive=True,
        )
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
    _pool = None
