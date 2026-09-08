"""Data exfiltration: large sustained outbound transfer to one destination."""

from __future__ import annotations

import random

from simulator.models import APP_HOSTS, DB_HOSTS, make_event, rand_external_ip, rand_internal_ip


def data_exfiltration(*, source_ip: str | None = None, total_mib: int | None = None) -> list[dict]:
    src = source_ip or rand_internal_ip()
    dst = rand_external_ip()
    host = random.choice(APP_HOSTS + DB_HOSTS)
    total_mib = total_mib or random.randint(120, 900)
    chunks = random.randint(15, 40)
    per_chunk = int(total_mib * 1024 * 1024 / chunks)

    events: list[dict] = []
    for i in range(chunks):
        jitter = random.uniform(0.7, 1.3)
        events.append(
            make_event(
                source=host,
                source_type="application",
                event_type="network_flow",
                severity="medium",
                status="allowed",
                source_ip=src,
                destination_ip=dst,
                destination_port=random.choice([443, 22, 8443, 9001]),
                service="api-gateway",
                action="outbound transfer",
                bytes_out=int(per_chunk * jitter),
                bytes_in=random.randint(200, 1500),
                message=f"flow {src} -> {dst} chunk {i + 1}/{chunks}",
                metadata={"exfil": True, "protocol": "tls"},
            )
        )
    return events
