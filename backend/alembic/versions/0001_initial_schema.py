"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "security_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("source_ip", sa.String(45)),
        sa.Column("destination_ip", sa.String(45)),
        sa.Column("destination_port", sa.Integer()),
        sa.Column("username", sa.String(255)),
        sa.Column("service", sa.String(128)),
        sa.Column("action", sa.String(255)),
        sa.Column("status", sa.String(32)),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("bytes_out", sa.BigInteger(), server_default="0"),
        sa.Column("bytes_in", sa.BigInteger(), server_default="0"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
    )
    op.create_index("ix_security_events_source", "security_events", ["source"])
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_source_ip", "security_events", ["source_ip"])
    op.create_index("ix_security_events_username", "security_events", ["username"])
    op.create_index("ix_security_events_severity", "security_events", ["severity"])
    op.create_index("ix_events_ts_desc", "security_events", [sa.text("timestamp DESC")])
    op.create_index(
        "ix_events_type_ts", "security_events", ["event_type", sa.text("timestamp DESC")]
    )
    op.create_index(
        "ix_events_srcip_ts", "security_events", ["source_ip", sa.text("timestamp DESC")]
    )
    op.create_index(
        "ix_events_severity_ts", "security_events", ["severity", sa.text("timestamp DESC")]
    )

    op.create_table(
        "alerts",
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.String(32), nullable=False),
        sa.Column("detection_kind", sa.String(16), nullable=False, server_default="rule"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_ip", sa.String(45)),
        sa.Column("affected_host", sa.String(255)),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("involved_users", postgresql.JSONB(), server_default="[]"),
        sa.Column("involved_hosts", postgresql.JSONB(), server_default="[]"),
        sa.Column("evidence", postgresql.JSONB(), server_default="[]"),
        sa.Column("recommended_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("correlation_key", sa.String(255), nullable=False),
        sa.Column("anomaly_score", sa.Float()),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rule_id", "correlation_key", "status", name="uq_alert_open_window"),
    )
    op.create_index("ix_alerts_rule_id", "alerts", ["rule_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_source_ip", "alerts", ["source_ip"])
    op.create_index(
        "ix_alerts_status_sev_lastseen",
        "alerts",
        ["status", "severity", sa.text("last_seen DESC")],
    )
    op.create_index("ix_alerts_lastseen_desc", "alerts", [sa.text("last_seen DESC")])

    op.create_table(
        "detection_rules",
        sa.Column("rule_id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("default_severity", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mitre_attack", postgresql.JSONB(), server_default="[]"),
        sa.Column("parameters", postgresql.JSONB(), server_default="{}"),
        sa.Column("recommended_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_detection_rules_category", "detection_rules", ["category"])

    op.create_table(
        "hosts",
        sa.Column("hostname", sa.String(255), primary_key=True),
        sa.Column("source_type", sa.String(64), nullable=False, server_default="unknown"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("alert_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(128)),
        sa.Column("request_id", sa.String(64)),
        sa.Column("detail", postgresql.JSONB(), server_default="{}"),
        sa.Column("note", sa.Text()),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    op.create_table(
        "users",
        sa.Column("username", sa.String(128), primary_key=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("audit_logs")
    op.drop_table("hosts")
    op.drop_table("detection_rules")
    op.drop_table("alerts")
    op.drop_table("security_events")
