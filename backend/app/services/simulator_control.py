"""Simulator control plane.

The API does not run the simulator; it publishes desired state to Redis
(``siem:simulator:control``).  The ``simulator`` container polls that key and
converges its generator rate / scenario to match.  This keeps the control path
distributed and lets the dashboard drive demos.
"""

from __future__ import annotations

import json
import time
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

CONTROL_KEY = "siem:simulator:control"
HEARTBEAT_KEY = "siem:simulator:heartbeat"
STATS_KEY = "siem:simulator:stats"

SCENARIOS = [
    "normal",
    "ssh_brute_force",
    "port_scan",
    "credential_attack",
    "privilege_escalation",
    "data_exfiltration",
    "web_attack",
    "mixed",
]


def _default_state() -> dict[str, Any]:
    return {
        "running": settings.simulator_autostart,
        "rate": settings.events_per_second,
        "scenario": settings.simulator_scenario,
        "attack_ratio": settings.simulator_attack_ratio,
        "burst": False,
        "updated_at": time.time(),
        "updated_by": "config",
    }


async def get_state(client: redis.Redis) -> dict[str, Any]:
    raw = await client.get(CONTROL_KEY)
    state = _default_state()
    if raw:
        try:
            state.update(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return state


async def set_state(client: redis.Redis, patch: dict[str, Any], *, actor: str = "api") -> dict[str, Any]:
    state = await get_state(client)
    if "scenario" in patch and patch["scenario"] not in SCENARIOS:
        raise ValueError(f"unknown scenario: {patch['scenario']}")
    if "rate" in patch:
        patch["rate"] = max(0, min(int(patch["rate"]), 20_000))
    if "attack_ratio" in patch:
        patch["attack_ratio"] = max(0.0, min(float(patch["attack_ratio"]), 1.0))
    state.update(patch)
    state["updated_at"] = time.time()
    state["updated_by"] = actor
    await client.set(CONTROL_KEY, json.dumps(state))
    return state


async def get_status(client: redis.Redis) -> dict[str, Any]:
    state = await get_state(client)
    hb_raw = await client.get(HEARTBEAT_KEY)
    stats_raw = await client.get(STATS_KEY)
    heartbeat = json.loads(hb_raw) if hb_raw else None
    stats = json.loads(stats_raw) if stats_raw else {}
    connected = bool(heartbeat) and (time.time() - heartbeat.get("ts", 0) < 15)
    return {
        "desired": state,
        "simulator_connected": connected,
        "last_heartbeat": heartbeat,
        "stats": stats,
    }
