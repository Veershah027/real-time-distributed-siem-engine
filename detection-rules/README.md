# Detection rule reference

These YAML files are a **human-readable catalogue** of the detectors implemented
in `backend/app/detection/rules/`. They mirror the code's default parameters and
MITRE mappings; the code — not this directory — is the source of truth at
runtime, and thresholds are overridden by the `SIEM_RULE_*` environment
variables (see [`../docs/detection-rules.md`](../docs/detection-rules.md)).

Layout follows the detector category:

| Directory | Rules |
|---|---|
| `authentication/` | RULE-001 brute force · RULE-002 password spray · RULE-004 privilege escalation · RULE-007 auth anomaly |
| `network/` | RULE-003 port scan · RULE-006 excessive outbound traffic |
| `database/` | RULE-005 suspicious database activity |
| `application/` | (reserved for future application-layer rules) |
