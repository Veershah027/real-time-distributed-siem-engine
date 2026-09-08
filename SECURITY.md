# Security Policy

This project is a **defensive security education / portfolio platform**. It
ingests and analyses *synthetic* security telemetry and simulates attacks
against *itself only*. It is not a production SIEM and should not be relied on to
protect a real environment without the hardening described below.

## Supported versions

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| tagged releases | best effort |
| older commits | ❌ |

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

1. Email the maintainer (see the `git log` author address) with:
   - a description and impact assessment,
   - reproduction steps or a proof of concept,
   - affected commit / version.
2. Expect an acknowledgement within **7 days**.
3. Coordinated disclosure: please allow a reasonable window for a fix before
   public discussion. Credit will be given unless you prefer otherwise.

## Security assumptions

- The stack runs on a **trusted single host** (a laptop or a private VM). All
  service ports are bound to `127.0.0.1` in `docker-compose.yml`.
- The **message broker is trusted** — there is no SASL/mTLS between services in
  the default topology.
- Dashboard authentication is **off by default** (`SIEM_AUTH_ENABLED=false`) for
  demo convenience. There are **no default production credentials**; the dev seed
  user is created from env vars only when auth is enabled.
- All ingested events are **synthetic** and are treated as **untrusted data** —
  validated, normalized, length/size-bounded, never executed.

## What is implemented

- Strict event validation & normalization (`app/schemas/event.py`) with tests in
  `backend/tests/test_security.py` and `test_event_schema.py`.
- 100% parameterized SQL (SQLAlchemy); no string-built queries.
- Redis-backed per-IP rate limiting on `/api/*` (fails open).
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `COOP`, `Permissions-Policy`; HSTS in production).
- Restricted CORS allow-list; methods limited to `GET/POST/PATCH/OPTIONS`.
- Request IDs on every request/response; structured JSON logs.
- Generic error responses in production (no stack traces leaked).
- Non-root containers; slim base images; pinned dependency versions.
- Alert-triage state machine enforced server-side; every change is audited
  (`audit_logs`).
- CI runs **Bandit** (SAST) and **pip-audit** (dependency CVEs) on every push.
- Optional LLM assistance is **off by default**, opt-in per alert, and can never
  override a deterministic detection.

## Known limitations

- No transport security between services in local/demo mode.
- No authn/authz on the WebSocket channel (it is read-only).
- `pip-audit` in CI is advisory (does not fail the build) so an upstream CVE with
  no fix does not block development — review its output on each run.
- The frontend bundle is not subresource-integrity pinned.
- No secret management integration — secrets come from `.env` / environment.
- Detection rules are demonstration rules; do not treat their verdicts as
  authoritative for a real environment.

## Local-only attack simulation — warning

The `simulator/` component generates **fabricated** log events describing attack
patterns (brute force, port scan, SQL injection strings, exfiltration flows,
etc.). It:

- **never** sends traffic to, scans, or interacts with any real host or network;
- uses only RFC 1918 and `TEST-NET` (`192.0.2.0/24`, `198.51.100.0/24`,
  `203.0.113.0/24`) addresses — enforced by `simulator/tests/test_generators.py`;
- contains **no** real exploit code — SQL "attacks" are strings written to a log
  field and pattern-matched, never executed.

Do not modify the simulator to target real infrastructure. Doing so may be
illegal and is explicitly out of scope for this project.

## Hardening before any shared/non-local deployment

See [`docs/threat-model.md`](docs/threat-model.md#hardening-checklist-for-a-non-local-deployment).
