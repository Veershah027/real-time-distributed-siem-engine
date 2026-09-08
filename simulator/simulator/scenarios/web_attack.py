"""Web attack: suspicious paths, scanners, repeated 4xx/5xx from one IP."""

from __future__ import annotations

import random

from simulator.models import WEB_HOSTS, make_event, rand_external_ip

_SUSPICIOUS_PATHS = [
    "/.env", "/.git/config", "/wp-login.php", "/admin", "/phpmyadmin",
    "/api/../../etc/passwd", "/actuator/env", "/server-status", "/.aws/credentials",
    "/cgi-bin/test.cgi", "/api/users?id=1%20OR%201=1", "/shell.php", "/vendor/phpunit",
]


def web_attack(*, source_ip: str | None = None) -> list[dict]:
    src = source_ip or rand_external_ip()
    web = random.choice(WEB_HOSTS)
    events: list[dict] = []
    for _ in range(random.randint(18, 40)):
        path = random.choice(_SUSPICIOUS_PATHS)
        status = random.choices([404, 403, 401, 500, 200], weights=[50, 20, 15, 10, 5])[0]
        events.append(
            make_event(
                source=web,
                source_type="web_server",
                event_type="http_request",
                severity="medium",
                status="error" if status >= 400 else "success",
                source_ip=src,
                service="nginx",
                action=f"GET {path}",
                destination_port=443,
                bytes_out=random.randint(120, 900),
                message=f'GET {path} {status} "sqlmap/1.7"',
                metadata={"http_status": status, "path": path, "user_agent": "sqlmap/1.7"},
            )
        )
    return events
