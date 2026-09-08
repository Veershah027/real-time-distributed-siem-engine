"""Simulator configuration (env-driven, matches the project's .env)."""

from __future__ import annotations

import os


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


class SimulatorConfig:
    """Resolved once at import from the environment; fields are mutated by the CLI."""

    def __init__(self) -> None:
        self.kafka_bootstrap_servers = _get("SIEM_KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
        self.kafka_topic = _get("SIEM_KAFKA_TOPIC_EVENTS", "siem.events.raw")
        redis_host = _get("REDIS_HOST", "localhost")
        redis_port = _get("REDIS_PORT", "6379")
        redis_db = _get("REDIS_DB", "0")
        self.redis_url = _get("SIEM_REDIS_URL", f"redis://{redis_host}:{redis_port}/{redis_db}")
        self.events_per_second = int(_get("SIEM_EVENTS_PER_SECOND", "50"))
        self.scenario = _get("SIEM_SIMULATOR_SCENARIO", "normal")
        self.attack_ratio = float(_get("SIEM_SIMULATOR_ATTACK_RATIO", "0.05"))
        self.autostart = _get("SIEM_SIMULATOR_AUTOSTART", "false").lower() == "true"
        self.sink = _get("SIEM_SIMULATOR_SINK", "kafka")  # kafka | console
        self.control_via_redis = _get("SIEM_SIMULATOR_CONTROL_VIA_REDIS", "true").lower() == "true"


CONFIG = SimulatorConfig()
