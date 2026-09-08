# Detection Rules & Anomaly Detection

All detectors implement `app.detection.base.Detector`. Rule state lives in Redis
sliding windows (`app.detection.windows.WindowStore`), so detection is
horizontally scalable and thresholds are time-bounded.

> These are **demonstration** rules for detection-engineering practice. They are
> not a tuned production ruleset and will produce false positives on real
> traffic without calibration.

## Common `Detection` fields

| Field | Meaning |
|---|---|
| `rule_id` | e.g. `RULE-001` |
| `kind` | `rule` \| `anomaly` \| `ml` |
| `severity` | `info`…`critical` (correlator keeps the max seen) |
| `confidence` | 0–1, grows as evidence exceeds the threshold |
| `correlation_key` | groups events into one alert (e.g. `srcip:203.0.113.9`) |
| `event_count_hint` | window size at trigger time |
| `evidence` | capped list of `{event_id, timestamp, summary}` |
| `recommended_action` | analyst guidance shown in the alert detail |

---

## RULE-001 — SSH / service brute force

**Category** authentication · **MITRE** T1110.001 · **Severity** HIGH
(→ CRITICAL if a login subsequently succeeds from the same IP inside the window).

**Trigger.** More than `max_failures` `authentication_failure` events from one
`source_ip` within `window_seconds`. An `authentication_success` from an IP that
is already over the threshold escalates the alert to CRITICAL
(`account_breached = true`).

| Env var | Default |
|---|---|
| `SIEM_RULE_BRUTEFORCE_MAX_FAILURES` | 10 |
| `SIEM_RULE_BRUTEFORCE_WINDOW_SECONDS` | 60 |

**Correlation key** `srcip:<ip>` · **Confidence** `0.6 + 0.02·(count − threshold)`, +0.15 on breach.

---

## RULE-002 — Password spraying

**Category** authentication · **MITRE** T1110.003 · **Severity** HIGH

**Trigger.** One `source_ip` produces `authentication_failure` against more than
`unique_users` distinct usernames within `window_seconds` (low-and-slow — few
attempts per account, many accounts).

| Env var | Default |
|---|---|
| `SIEM_RULE_SPRAY_UNIQUE_USERS` | 8 |
| `SIEM_RULE_SPRAY_WINDOW_SECONDS` | 120 |

**Correlation key** `srcip:<ip>:spray`.

---

## RULE-003 — Port scanning

**Category** network · **MITRE** T1046 · **Severity** HIGH

**Trigger.** One `source_ip` contacts more than `unique_ports` distinct
`destination_port` values within `window_seconds`, across
`connection_attempt` / `firewall_deny` / `firewall_allow` / `network_flow`
events.

| Env var | Default |
|---|---|
| `SIEM_RULE_PORTSCAN_UNIQUE_PORTS` | 20 |
| `SIEM_RULE_PORTSCAN_WINDOW_SECONDS` | 30 |

**Correlation key** `srcip:<ip>:portscan` · metadata includes a port sample and scan rate.

---

## RULE-004 — Privilege escalation

**Category** authentication · **MITRE** T1548, T1078 · **Severity** HIGH

**Trigger.** A privileged action (`privilege_escalation` event, or an `action`
matching `sudo`, `usermod`, `pkexec`, `net localgroup administrators`, …) where
**at least one** risk factor holds:

- the actor is **not** a known privileged account (`metadata.user_role` /
  username not in `privileged_roles`);
- the action occurred **off-hours** (22:00–05:59 UTC);
- the host reported an **explicit** `privilege_escalation` event.

Confidence accumulates per factor; a failed attempt adds a little more.

**Correlation key** `host:<host>:user:<user>:privesc`.

---

## RULE-005 — Suspicious database activity

**Category** database · **MITRE** T1190, T1213 · **Severity** MEDIUM (→ HIGH for
high-weight patterns).

**Trigger.** The query text in a synthetic `db_query` / `db_error` event
(`metadata.query` or `message`) matches known injection/exfil patterns:
`UNION SELECT`, `OR 1=1`, stacked queries, `information_schema` enumeration,
`load_file` / `INTO OUTFILE` / `xp_cmdshell`, time-based blind (`SLEEP(`,
`WAITFOR DELAY`), or an abnormally large result set (`rows_returned ≥
large_rowcount`, default 5000).

**No SQL is executed** — this is pattern matching on log text only.

**Correlation key** `db:<host>:user:<user|ip>:sqli`.

---

## RULE-006 — Excessive outbound traffic

**Category** network · **MITRE** T1041, T1048 · **Severity** MEDIUM (→ HIGH at
≥ 3× threshold).

**Trigger.** Sliding-window sum of `bytes_out` for a `source_ip → destination_ip`
pair exceeds `bytes_threshold` within `window_seconds`.

| Env var | Default |
|---|---|
| `SIEM_RULE_EXFIL_BYTES_THRESHOLD` | 52428800 (50 MiB) |
| `SIEM_RULE_EXFIL_WINDOW_SECONDS` | 60 |

**Correlation key** `srcip:<ip>:exfil`.

---

## RULE-007 — Authentication anomaly

**Category** authentication · **MITRE** T1078 · **Severity** MEDIUM (→ HIGH if a
successful login and ≥ threshold+2 distinct IPs).

**Trigger.** One account authenticates from more than `distinct_ips` distinct
source IPs within `window_seconds` (a proxy for impossible-travel / shared
credentials). Defaults: 4 IPs / 300 s (not currently exposed as env vars —
edit `default_params`).

**Correlation key** `user:<username>:authgeo`.

---

## <a name="anomaly"></a>ANOM-001 — Statistical anomaly (EWMA z-score)

`app.detection.anomaly.StatisticalAnomalyDetector`.

Per named metric, an exponentially-weighted mean and variance are kept in Redis
(`siem:anomaly:<metric>`, 7-day TTL). On each per-minute observation:

```
z = (value − mean) / sqrt(var)
anomalous  ⟺  n ≥ min_samples  AND  |z| ≥ z_threshold
anomaly_score = min(1, 0.5 + 0.5·(1 − e^(−(|z| − z_threshold)² / 8)))
```

The EWMA update dampens `alpha` for extreme points so a single spike does not
poison the baseline. Metrics fed each minute: `events_per_min`,
`auth_failures_per_min`, `unique_source_ips`, `outbound_mib_per_min`,
`db_errors_per_min`, `firewall_denies_per_min`.

| Env var | Default |
|---|---|
| `SIEM_ANOMALY_ZSCORE_THRESHOLD` | 3.5 |
| `SIEM_ANOMALY_EWMA_ALPHA` | 0.3 |
| `SIEM_ANOMALY_MIN_SAMPLES` | 20 |

Output carries `anomaly_reason`, e.g.
*"events_per_min = 4200.0 is 7.3σ above the rolling baseline of 103.4 ± 12.1
(n=41)"*.

---

## ML-001 — Isolation Forest outlier (optional)

`app.detection.ml.IsolationForestDetector`. Disabled unless `SIEM_ENABLE_ML=true`
**and** the `ml` extra is installed (`pip install -e ".[ml]"`).

Trains on a rolling buffer of recent per-minute feature vectors and flags
outliers (`contamination=0.05`). **Research/demo model only** — it never
overrides a deterministic rule; its alerts are explicitly advisory.

---

## Tuning workflow

1. Watch the Detection Rules page for firing frequency.
2. Adjust thresholds via env vars, `docker compose up -d` to apply.
3. For anomaly noise, raise `SIEM_ANOMALY_ZSCORE_THRESHOLD` or
   `SIEM_ANOMALY_MIN_SAMPLES`.
4. Mark false positives in the UI — the rate shows up in `/api/metrics`
   (`false_positive_rate`).
