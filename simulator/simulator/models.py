"""Synthetic entity pools + event construction."""

from __future__ import annotations

import ipaddress
import random
import uuid
from datetime import UTC, datetime
from typing import Any

# --- fabricated enterprise inventory -------------------------------------- #
SSH_HOSTS = [f"ssh-server-{i:02d}" for i in range(1, 6)]
WEB_HOSTS = [f"web-{i:02d}" for i in range(1, 5)]
DB_HOSTS = [f"db-{i:02d}" for i in range(1, 4)]
APP_HOSTS = [f"app-{i:02d}" for i in range(1, 6)]
FW_HOSTS = [f"fw-{i:02d}" for i in range(1, 3)]
IDP_HOSTS = ["idp-01", "idp-02"]
DNS_HOSTS = ["dns-01", "dns-02"]

USERS = [
    "alice",
    "bob",
    "carol",
    "dave",
    "erin",
    "frank",
    "grace",
    "heidi",
    "ivan",
    "judy",
    "mallory",
    "olivia",
    "peggy",
    "trent",
    "victor",
    "walter",
    "svc_backup",
    "svc_ci",
    "svc_monitoring",
    "jenkins",
]
ADMINS = {"root", "admin", "administrator"}
PRIVILEGED_USERS = {"alice", "trent", "svc_ci"}

SERVICES = ["ssh", "sshd", "nginx", "postgres", "api-gateway", "auth-service", "cron"]
HTTP_PATHS = [
    "/",
    "/login",
    "/api/health",
    "/api/users",
    "/api/orders",
    "/static/app.js",
    "/dashboard",
    "/api/reports",
    "/favicon.ico",
]
HTTP_METHODS = ["GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"]
DNS_NAMES = [
    "updates.internal",
    "pkg.repo.internal",
    "api.partner.example",
    "cdn.assets.example",
    "smtp.corp.internal",
    "ntp.pool.internal",
]

INTERNAL_NET = ipaddress.ip_network("10.42.0.0/16")
EXTERNAL_SAMPLE = ipaddress.ip_network("203.0.113.0/24")  # TEST-NET-3 (safe, non-routable)


def rand_internal_ip() -> str:
    return str(INTERNAL_NET[random.randint(1, INTERNAL_NET.num_addresses - 2)])


def rand_external_ip() -> str:
    return str(EXTERNAL_SAMPLE[random.randint(1, 254)])


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def make_event(
    *,
    source: str,
    source_type: str,
    event_type: str,
    severity: str = "info",
    status: str | None = None,
    source_ip: str | None = None,
    destination_ip: str | None = None,
    destination_port: int | None = None,
    username: str | None = None,
    service: str | None = None,
    action: str | None = None,
    message: str | None = None,
    bytes_out: int = 0,
    bytes_in: int = 0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "source": source,
        "source_type": source_type,
        "event_type": event_type,
        "severity": severity,
        "status": status,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "destination_port": destination_port,
        "username": username,
        "service": service,
        "action": action,
        "message": message,
        "bytes_out": bytes_out,
        "bytes_in": bytes_in,
        "metadata": metadata or {},
    }
