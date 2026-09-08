"""Simulator configuration (env-driven, matches the project's .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(slots=True)
class SimulatorConfig:
    kafka_bootstrap_servers: str = _get("SIEM_KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    kafka_topic: str = _get("SIEM_KAFKA_TOPIC_EVENTS", "siem.events.raw")
    redis_url: str = _get(
        "SIEM_REDIS_URL",
        f"redis://{_get('REDIS_HOST', 'localhost')}:{_get('REDIS_PORT', '6379')}/{_get('REDIS_DB', '0')}",
    )
    events_per_second: int = int(_get("SIEM_EVENTS_PER_SECOND", "50"))
    scenario: str = _get("SIEM_SIMULATOR_SCENARIO", "normal")
    attack_ratio: float = float(_get("SIEM_SIMULATOR_ATTACK_RATIO", "0.05"))
    autostart: bool = _get("SIEM_SIMULATOR_AUTOSTART", "false").lower() == "true"
    sink: str = _get("SIEM_SIMULATOR_SINK", "kafka")  # kafka | console
    control_via_redis: bool = _get("SIEM_SIMULATOR_CONTROL_VIA_REDIS", "true").lower() == "true"


CONFIG = SimulatorConfig()
