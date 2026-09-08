"""Credential attack / password spraying: one IP, one password, many accounts."""

from __future__ import annotations

import random

from simulator.models import IDP_HOSTS, USERS, make_event, rand_external_ip


def credential_attack(*, accounts: int | None = None, source_ip: str | None = None) -> list[dict]:
    accounts = accounts or random.randint(12, 24)
    src = source_ip or rand_external_ip()
    host = random.choice(IDP_HOSTS)
    targets = random.sample(USERS, k=min(accounts, len(USERS)))

    events: list[dict] = []
    for user in targets:
        events.append(
            make_event(
                source=host,
                source_type="identity",
                event_type="authentication_failure",
                severity="medium",
                status="failure",
                source_ip=src,
                username=user,
                service="auth-service",
                action="password auth",
                message=f"authentication failure for {user} from {src}",
                metadata={"spray": True, "user_role": "user"},
            )
        )
    # occasional lucky hit
    if random.random() > 0.7:
        user = random.choice(targets)
        events.append(
            make_event(
                source=host,
                source_type="identity",
                event_type="authentication_success",
                severity="high",
                status="success",
                source_ip=src,
                username=user,
                service="auth-service",
                action="password auth",
                message=f"authentication success for {user} from {src}",
                metadata={"spray": True, "user_role": "user"},
            )
        )
    return events
