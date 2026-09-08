"""Privilege escalation: a normal user performs admin actions, often off-hours."""

from __future__ import annotations

import random

from simulator.models import APP_HOSTS, SSH_HOSTS, make_event, rand_internal_ip

_ESCALATION_ACTIONS = [
    "sudo su -",
    "sudo cat /etc/shadow",
    "usermod -aG sudo {user}",
    "sudo visudo",
    "pkexec /bin/bash",
    "net localgroup administrators {user} /add",
    "chmod 4755 /tmp/.x",
]


def privilege_escalation(*, user: str | None = None, source_ip: str | None = None) -> list[dict]:
    user = user or random.choice(["bob", "carol", "dave", "erin", "walter"])
    src = source_ip or rand_internal_ip()
    host = random.choice(SSH_HOSTS + APP_HOSTS)
    events: list[dict] = []

    events.append(
        make_event(
            source=host,
            source_type="linux_server",
            event_type="authentication_success",
            severity="info",
            status="success",
            source_ip=src,
            username=user,
            service="ssh",
            action="ssh login",
            message=f"Accepted publickey for {user}",
            metadata={"user_role": "user"},
        )
    )
    for _ in range(random.randint(2, 4)):
        action = random.choice(_ESCALATION_ACTIONS).format(user=user)
        failed = random.random() > 0.6
        events.append(
            make_event(
                source=host,
                source_type="linux_server",
                event_type="privilege_escalation",
                severity="high",
                status="failure" if failed else "success",
                source_ip=src,
                username=user,
                service="sudo",
                action=action,
                message=f"{user} : {'FAILED ' if failed else ''}command={action}",
                metadata={"user_role": "user", "tty": "pts/0"},
            )
        )
    return events
