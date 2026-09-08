"""Synthetic SQL-injection-style database logs. No SQL is executed anywhere."""

from __future__ import annotations

import random

from simulator.models import DB_HOSTS, WEB_HOSTS, make_event, rand_external_ip

_MALICIOUS_QUERIES = [
    "SELECT * FROM users WHERE name = '' OR 1=1 -- '",
    "SELECT id, pw_hash FROM users WHERE email = 'x' UNION SELECT username, password FROM admins -- ",
    "SELECT * FROM products WHERE id = 1; DROP TABLE sessions; --",
    "SELECT * FROM information_schema.tables --",
    "SELECT load_file('/etc/passwd')",
    "SELECT * FROM orders WHERE id = 1 AND SLEEP(5)",
    "'; INSERT INTO admins (username, password) VALUES ('mallory','x'); --",
    "SELECT * FROM customers WHERE zip = 1 OR 1=1 INTO OUTFILE '/tmp/dump.csv'",
]


def sql_attack(*, source_ip: str | None = None) -> list[dict]:
    src = source_ip or rand_external_ip()
    web = random.choice(WEB_HOSTS)
    db = random.choice(DB_HOSTS)
    events: list[dict] = []
    for _ in range(random.randint(4, 9)):
        q = random.choice(_MALICIOUS_QUERIES)
        rows = random.choice([0, 0, 1, 12000, 45000])
        errored = random.random() > 0.5
        events.append(
            make_event(
                source=db,
                source_type="database",
                event_type="db_error" if errored else "db_query",
                severity="high",
                status="error" if errored else "success",
                source_ip=src,
                username="svc_api",
                service="postgres",
                action="query",
                message=q,
                metadata={
                    "query": q,
                    "rows_returned": rows,
                    "origin_host": web,
                    "error": "syntax error near '--'" if errored else None,
                },
            )
        )
    return events
