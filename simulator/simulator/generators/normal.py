"""Baseline "business as usual" enterprise events."""

from __future__ import annotations

import random
from typing import Any

from simulator.models import (
    APP_HOSTS,
    DB_HOSTS,
    DNS_HOSTS,
    DNS_NAMES,
    FW_HOSTS,
    HTTP_METHODS,
    HTTP_PATHS,
    IDP_HOSTS,
    SSH_HOSTS,
    USERS,
    WEB_HOSTS,
    make_event,
    rand_external_ip,
    rand_internal_ip,
)

_BENIGN_QUERIES = [
    "SELECT id, name FROM users WHERE id = $1",
    "SELECT * FROM orders WHERE customer_id = $1 ORDER BY created_at DESC LIMIT 50",
    "UPDATE sessions SET last_seen = now() WHERE token = $1",
    "INSERT INTO audit_log (actor, action) VALUES ($1, $2)",
    "SELECT count(*) FROM events WHERE ts > now() - interval '1 hour'",
]


def _ssh_login() -> dict[str, Any]:
    ok = random.random() > 0.12
    user = random.choice(USERS)
    return make_event(
        source=random.choice(SSH_HOSTS),
        source_type="linux_server",
        event_type="authentication_success" if ok else "authentication_failure",
        severity="info" if ok else "low",
        status="success" if ok else "failure",
        source_ip=rand_internal_ip(),
        username=user,
        service="ssh",
        action="ssh login",
        message=f"{'Accepted' if ok else 'Failed'} password for {user} from ssh",
        metadata={"user_role": "admin" if user in {"alice", "trent"} else "user"},
    )


def _http_request() -> dict[str, Any]:
    status = random.choices([200, 200, 200, 204, 301, 404, 500], weights=[60, 15, 10, 5, 4, 4, 2])[0]
    method = random.choice(HTTP_METHODS)
    path = random.choice(HTTP_PATHS)
    return make_event(
        source=random.choice(WEB_HOSTS),
        source_type="web_server",
        event_type="http_request",
        severity="info" if status < 400 else "low",
        status="success" if status < 400 else "error",
        source_ip=rand_internal_ip() if random.random() > 0.4 else rand_external_ip(),
        service="nginx",
        action=f"{method} {path}",
        destination_port=443,
        bytes_out=random.randint(200, 24_000),
        bytes_in=random.randint(80, 2_000),
        message=f'{method} {path} {status}',
        metadata={"http_status": status, "method": method, "path": path},
    )


def _db_query() -> dict[str, Any]:
    q = random.choice(_BENIGN_QUERIES)
    return make_event(
        source=random.choice(DB_HOSTS),
        source_type="database",
        event_type="db_query",
        severity="info",
        status="success",
        source_ip=rand_internal_ip(),
        username=random.choice(["svc_api", "svc_reports", "app"]),
        service="postgres",
        action="query",
        message=q,
        metadata={"query": q, "rows_returned": random.randint(0, 120), "duration_ms": random.randint(1, 90)},
    )


def _firewall() -> dict[str, Any]:
    allow = random.random() > 0.25
    return make_event(
        source=random.choice(FW_HOSTS),
        source_type="firewall",
        event_type="firewall_allow" if allow else "firewall_deny",
        severity="info" if allow else "low",
        status="allowed" if allow else "denied",
        source_ip=rand_internal_ip() if random.random() > 0.5 else rand_external_ip(),
        destination_ip=rand_internal_ip(),
        destination_port=random.choice([80, 443, 22, 3389, 5432, 8080, 53]),
        service="firewall",
        action="ACCEPT" if allow else "DROP",
        bytes_out=random.randint(0, 4000),
        message=f"{'ACCEPT' if allow else 'DROP'} tcp",
    )


def _dns() -> dict[str, Any]:
    name = random.choice(DNS_NAMES)
    return make_event(
        source=random.choice(DNS_HOSTS),
        source_type="dns",
        event_type="dns_query",
        severity="info",
        status="success",
        source_ip=rand_internal_ip(),
        destination_port=53,
        service="dns",
        action=f"query {name}",
        message=f"A? {name}",
        metadata={"qname": name, "qtype": "A"},
    )


def _app_event() -> dict[str, Any]:
    return make_event(
        source=random.choice(APP_HOSTS),
        source_type="application",
        event_type="application_event",
        severity="info",
        status="success",
        username=random.choice(USERS),
        service="api-gateway",
        action=random.choice(["order.created", "report.exported", "profile.updated", "cache.refreshed"]),
        message="application event",
    )


def _logout() -> dict[str, Any]:
    return make_event(
        source=random.choice(SSH_HOSTS + APP_HOSTS),
        source_type="linux_server",
        event_type="logout",
        severity="info",
        status="success",
        source_ip=rand_internal_ip(),
        username=random.choice(USERS),
        service="ssh",
        action="logout",
        message="session closed",
    )


def _scheduled_job() -> dict[str, Any]:
    return make_event(
        source=random.choice(APP_HOSTS),
        source_type="scheduler",
        event_type="scheduled_job",
        severity="info",
        status="success",
        username="cron",
        service="cron",
        action=random.choice(["backup.nightly", "rotate.logs", "sync.ldap", "vacuum.db"]),
        message="cron job completed",
    )


def _idp_event() -> dict[str, Any]:
    ok = random.random() > 0.1
    user = random.choice(USERS)
    return make_event(
        source=random.choice(IDP_HOSTS),
        source_type="identity",
        event_type="authentication_success" if ok else "authentication_failure",
        severity="info" if ok else "low",
        status="success" if ok else "failure",
        source_ip=rand_internal_ip() if random.random() > 0.5 else rand_external_ip(),
        username=user,
        service="auth-service",
        action="SAML assertion" if ok else "SAML auth failed",
        message=f"IdP auth {'ok' if ok else 'failed'} for {user}",
        metadata={"user_role": "user"},
    )


_MIX = (
    (_http_request, 34),
    (_firewall, 18),
    (_dns, 12),
    (_db_query, 12),
    (_ssh_login, 9),
    (_app_event, 6),
    (_idp_event, 4),
    (_logout, 3),
    (_scheduled_job, 2),
)
_FUNCS = [f for f, _ in _MIX]
_WEIGHTS = [w for _, w in _MIX]


def normal_event() -> dict[str, Any]:
    return random.choices(_FUNCS, weights=_WEIGHTS)[0]()
