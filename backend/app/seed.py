"""Seed the ``detection_rules`` catalogue from the code-defined detectors.

Idempotent: run on every container start after migrations.

    python -m app.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.logging import get_logger
from app.detection.rules import RULE_DETECTORS
from app.models import DetectionRuleRow
from app.storage.db import dispose_engine, session_scope

log = get_logger("seed")

_STATISTICAL = [
    {
        "rule_id": "ANOM-001",
        "name": "Statistical traffic anomaly (EWMA z-score)",
        "category": "anomaly",
        "description": "Per-minute metric deviates beyond the configured z-score from a rolling baseline.",
        "default_severity": "medium",
        "mitre_attack": [],
        "parameters": {},
        "recommended_action": "Investigate what changed in the environment during the flagged minute.",
    },
    {
        "rule_id": "ML-001",
        "name": "Isolation Forest outlier (optional demo model)",
        "category": "anomaly",
        "description": "Unsupervised outlier detection on per-minute feature vectors. Research/demo only.",
        "default_severity": "medium",
        "mitre_attack": [],
        "parameters": {},
        "recommended_action": "Confirm with deterministic rules before acting.",
    },
]


async def seed_rules() -> int:
    rows: list[dict] = []
    for cls in RULE_DETECTORS:
        d = cls()  # type: ignore[abstract]
        rows.append(
            {
                "rule_id": d.rule_id,
                "name": d.name,
                "category": d.category,
                "description": (d.__doc__ or "").strip().split("\n")[0],
                "default_severity": d.default_severity.value,
                "enabled": True,
                "mitre_attack": d.mitre_attack,
                "parameters": d.default_params,
                "recommended_action": d.recommended_action,
            }
        )
    rows.extend({**r, "enabled": True} for r in _STATISTICAL)

    async with session_scope() as session:
        stmt = pg_insert(DetectionRuleRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["rule_id"],
            set_={
                "name": stmt.excluded.name,
                "category": stmt.excluded.category,
                "description": stmt.excluded.description,
                "default_severity": stmt.excluded.default_severity,
                "mitre_attack": stmt.excluded.mitre_attack,
                "parameters": stmt.excluded.parameters,
                "recommended_action": stmt.excluded.recommended_action,
            },
        )
        await session.execute(stmt)
    log.info("rules_seeded", count=len(rows))
    return len(rows)


async def _main() -> None:
    try:
        await seed_rules()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(_main())
