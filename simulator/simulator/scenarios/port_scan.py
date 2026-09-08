"""Port scan: one source IP hits many destination ports quickly."""

from __future__ import annotations

import random

from simulator.models import FW_HOSTS, make_event, rand_external_ip, rand_internal_ip

_COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995,
                 1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]


def port_scan(*, ports: int | None = None, source_ip: str | None = None) -> list[dict]:
    ports = ports or random.randint(25, 60)
    src = source_ip or rand_external_ip()
    target = rand_internal_ip()
    fw = random.choice(FW_HOSTS)
    port_pool = list(_COMMON_PORTS) + [random.randint(1, 65535) for _ in range(ports)]
    chosen = random.sample(port_pool, k=min(ports, len(port_pool)))

    events: list[dict] = []
    for p in chosen:
        blocked = random.random() > 0.15
        events.append(
            make_event(
                source=fw,
                source_type="firewall",
                event_type="firewall_deny" if blocked else "connection_attempt",
                severity="medium",
                status="denied" if blocked else "failure",
                source_ip=src,
                destination_ip=target,
                destination_port=int(p),
                service="firewall",
                action="DROP" if blocked else "SYN",
                message=f"{'DROP' if blocked else 'SYN'} tcp {src} -> {target}:{p}",
                metadata={"scan": True},
            )
        )
    return events
