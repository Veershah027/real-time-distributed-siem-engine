"""Shared enumerations for events and alerts."""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class SourceType(StrEnum):
    LINUX_SERVER = "linux_server"
    WEB_SERVER = "web_server"
    FIREWALL = "firewall"
    DATABASE = "database"
    APPLICATION = "application"
    IDENTITY = "identity"
    DNS = "dns"
    SCHEDULER = "scheduler"
    UNKNOWN = "unknown"


class EventType(StrEnum):
    # authentication
    AUTH_SUCCESS = "authentication_success"
    AUTH_FAILURE = "authentication_failure"
    LOGOUT = "logout"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    # network
    FIREWALL_ALLOW = "firewall_allow"
    FIREWALL_DENY = "firewall_deny"
    CONNECTION_ATTEMPT = "connection_attempt"
    DNS_QUERY = "dns_query"
    NETWORK_FLOW = "network_flow"
    # web
    HTTP_REQUEST = "http_request"
    # database
    DB_QUERY = "db_query"
    DB_ERROR = "db_error"
    # application / system
    APP_EVENT = "application_event"
    SCHEDULED_JOB = "scheduled_job"
    CONFIG_CHANGE = "config_change"
    UNKNOWN = "unknown"


class EventStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    ALLOWED = "allowed"
    DENIED = "denied"
    BLOCKED = "blocked"
    ERROR = "error"
    INFO = "info"


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class DetectionKind(StrEnum):
    RULE = "rule"
    ANOMALY = "anomaly"
    ML = "ml"
