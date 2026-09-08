"""Attack scenario generators.

Each function returns a *complete* synthetic attack instance as a list of
events (already time-ordered).  The engine paces these out and interleaves
normal background traffic.  Nothing here touches a real system.
"""

from __future__ import annotations

from collections.abc import Callable

from simulator.scenarios.credential_attack import credential_attack
from simulator.scenarios.data_exfiltration import data_exfiltration
from simulator.scenarios.port_scan import port_scan
from simulator.scenarios.privilege_escalation import privilege_escalation
from simulator.scenarios.sql_attack import sql_attack
from simulator.scenarios.ssh_brute_force import ssh_brute_force
from simulator.scenarios.web_attack import web_attack

SCENARIOS: dict[str, Callable[..., list[dict]]] = {
    "ssh_brute_force": ssh_brute_force,
    "port_scan": port_scan,
    "credential_attack": credential_attack,
    "privilege_escalation": privilege_escalation,
    "data_exfiltration": data_exfiltration,
    "sql_attack": sql_attack,
    "web_attack": web_attack,
}

__all__ = ["SCENARIOS"]
