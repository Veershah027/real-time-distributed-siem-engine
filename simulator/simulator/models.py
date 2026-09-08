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


# Each user has a stable "home" workstation IP plus an occasional second device,
# so normal authentication traffic does NOT look like impossible-travel. Attack
# scenarios deliberately override the source IP.
_USER_HOME_IP: dict[str, str] = {}


def user_home_ip(username: str) -> str:
    if username not in _USER_HOME_IP:
        h = int.from_bytes(username.encode()[:4].ljust(4, b"\0"), "big")
        _USER_HOME_IP[username] = str(INTERNAL_NET[3000 + (h % 20000)])
    # ~10% of the time the user is on a second device (still 1-2 distinct IPs)
    if random.random() < 0.1:
        base = _USER_HOME_IP[username].rsplit(".", 1)[0]
        return f"{base}.{200 + (hash(username) % 40)}"
    return _USER_HOME_IP[username]


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
