from __future__ import annotations

import ipaddress

import pytest

from simulator.generators import normal_event
from simulator.scenarios import SCENARIOS

REQUIRED = {"event_id", "timestamp", "source", "source_type", "event_type"}


def _valid_ip(v):
    if v is None:
        return True
    try:
        ipaddress.ip_address(v)
        return True
    except ValueError:
        return False


def test_normal_event_shape():
    for _ in range(200):
        ev = normal_event()
        assert ev.keys() >= REQUIRED
        assert _valid_ip(ev["source_ip"])
        assert _valid_ip(ev["destination_ip"])
        assert ev["timestamp"].endswith("Z")


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_scenarios_produce_ordered_events(name):
    events = SCENARIOS[name]()
    assert len(events) >= 3
    for ev in events:
        assert ev.keys() >= REQUIRED
        assert _valid_ip(ev["source_ip"])


def test_brute_force_has_many_failures_from_one_ip():
    events = SCENARIOS["ssh_brute_force"](attempts=20, breach=True)
    ips = {e["source_ip"] for e in events}
    assert len(ips) == 1
    failures = [e for e in events if e["event_type"] == "authentication_failure"]
    assert len(failures) == 20
    assert events[-1]["event_type"] == "authentication_success"


def test_port_scan_hits_many_ports_from_one_ip():
    events = SCENARIOS["port_scan"](ports=40)
    ips = {e["source_ip"] for e in events}
    ports = {e["destination_port"] for e in events}
    assert len(ips) == 1
    assert len(ports) >= 20


_SQLI_MARKERS = (
    "'",
    "--",
    "union",
    "1=1",
    "drop",
    "information_schema",
    "load_file",
    "sleep",
    "outfile",
    "insert into admins",
)


def test_sql_attack_events_carry_query_text():
    events = SCENARIOS["sql_attack"]()
    assert all("query" in e["metadata"] for e in events)
    # every synthetic query is an injection-style string
    for e in events:
        q = e["metadata"]["query"].lower()
        assert any(marker in q for marker in _SQLI_MARKERS), q


def test_data_exfiltration_large_outbound():
    events = SCENARIOS["data_exfiltration"](total_mib=200)
    total = sum(e["bytes_out"] for e in events)
    assert total > 100 * 1024 * 1024


def test_scenarios_never_use_real_public_infrastructure():
    """All external IPs must be in TEST-NET blocks (documentation ranges)."""
    doc_nets = [
        ipaddress.ip_network("203.0.113.0/24"),
        ipaddress.ip_network("198.51.100.0/24"),
        ipaddress.ip_network("192.0.2.0/24"),
    ]
    for name, fn in SCENARIOS.items():
        for ev in fn():
            for key in ("source_ip", "destination_ip"):
                ip = ev.get(key)
                if not ip:
                    continue
                addr = ipaddress.ip_address(ip)
                assert addr.is_private or any(
                    addr in n for n in doc_nets
                ), f"{name} emitted non-safe IP {ip}"
