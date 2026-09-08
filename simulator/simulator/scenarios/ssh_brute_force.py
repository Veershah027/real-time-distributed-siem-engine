"""SSH brute force: many failures from one IP, then (often) a success."""

from __future__ import annotations

import random

from simulator.models import SSH_HOSTS, USERS, make_event, rand_external_ip


def ssh_brute_force(
    *, attempts: int | None = None, breach: bool | None = None, source_ip: str | None = None
) -> list[dict]:
    attempts = attempts or random.randint(15, 32)
    breach = random.random() > 0.45 if breach is None else breach
    src = source_ip or rand_external_ip()
    host = random.choice(SSH_HOSTS)
    target_users = random.sample(USERS, k=min(len(USERS), random.randint(2, 5)))

    events: list[dict] = []
    for i in range(attempts):
        user = random.choice(target_users) if i % 3 else "root"
        events.append(
            make_event(
                source=host,
                source_type="linux_server",
                event_type="authentication_failure",
                severity="medium",
                status="failure",
                source_ip=src,
                username=user,
                service="ssh",
                action="ssh login",
                destination_port=22,
                message=f"Failed password for {user} from {src} port {random.randint(30000, 61000)} ssh2",
                metadata={"attempt": i + 1, "user_role": "user"},
            )
        )
    if breach:
        user = random.choice(target_users)
        events.append(
            make_event(
                source=host,
                source_type="linux_server",
                event_type="authentication_success",
                severity="high",
                status="success",
                source_ip=src,
                username=user,
                service="ssh",
                action="ssh login",
                destination_port=22,
                message=f"Accepted password for {user} from {src} ssh2",
                metadata={"user_role": "user", "post_bruteforce": True},
            )
        )
    return events
