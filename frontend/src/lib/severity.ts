import type { AlertStatus, Severity } from "@/types";

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export const SEVERITY_META: Record<
  Severity,
  { label: string; color: string; text: string; bg: string; border: string }
> = {
  critical: {
    label: "Critical",
    color: "var(--sev-critical)",
    text: "text-sev-critical",
    bg: "bg-[var(--sev-critical)]/12",
    border: "border-[var(--sev-critical)]/40",
  },
  high: {
    label: "High",
    color: "var(--sev-high)",
    text: "text-sev-high",
    bg: "bg-[var(--sev-high)]/12",
    border: "border-[var(--sev-high)]/40",
  },
  medium: {
    label: "Medium",
    color: "var(--sev-medium)",
    text: "text-sev-medium",
    bg: "bg-[var(--sev-medium)]/12",
    border: "border-[var(--sev-medium)]/40",
  },
  low: {
    label: "Low",
    color: "var(--sev-low)",
    text: "text-sev-low",
    bg: "bg-[var(--sev-low)]/12",
    border: "border-[var(--sev-low)]/40",
  },
  info: {
    label: "Info",
    color: "var(--sev-info)",
    text: "text-sev-info",
    bg: "bg-[var(--sev-info)]/12",
    border: "border-[var(--sev-info)]/40",
  },
};

export const severityColor = (s: string): string =>
  SEVERITY_META[(s as Severity) in SEVERITY_META ? (s as Severity) : "info"].color;

export const STATUS_META: Record<AlertStatus, { label: string; color: string }> = {
  open: { label: "Open", color: "var(--sev-high)" },
  acknowledged: { label: "Acknowledged", color: "var(--accent)" },
  investigating: { label: "Investigating", color: "var(--sev-medium)" },
  resolved: { label: "Resolved", color: "var(--ok)" },
  false_positive: { label: "False Positive", color: "var(--idle)" },
};

export const WORKFLOW: AlertStatus[] = ["open", "acknowledged", "investigating", "resolved"];

/** Allowed next states — mirrors the backend transition table. */
export const NEXT_STATES: Record<AlertStatus, AlertStatus[]> = {
  open: ["acknowledged", "investigating", "resolved", "false_positive"],
  acknowledged: ["investigating", "resolved", "false_positive", "open"],
  investigating: ["acknowledged", "resolved", "false_positive", "open"],
  resolved: ["open"],
  false_positive: ["open"],
};

export const EVENT_TYPE_LABEL: Record<string, string> = {
  authentication_failure: "Auth Failure",
  authentication_success: "Auth Success",
  privilege_escalation: "Privilege Escalation",
  firewall_deny: "Firewall Deny",
  firewall_allow: "Firewall Allow",
  connection_attempt: "Connection Attempt",
  network_flow: "Network Flow",
  http_request: "HTTP Request",
  dns_query: "DNS Query",
  db_query: "DB Query",
  db_error: "DB Error",
  application_event: "App Event",
  scheduled_job: "Scheduled Job",
  logout: "Logout",
};

export const eventTypeLabel = (t: string): string =>
  EVENT_TYPE_LABEL[t] ?? t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
