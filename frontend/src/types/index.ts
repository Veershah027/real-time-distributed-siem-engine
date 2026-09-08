export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type AlertStatus = "open" | "acknowledged" | "resolved" | "false_positive";

export interface SecurityEvent {
  event_id: string;
  timestamp: string;
  ingested_at: string;
  source: string;
  source_type: string;
  event_type: string;
  source_ip: string | null;
  destination_ip: string | null;
  destination_port: number | null;
  username: string | null;
  service: string | null;
  action: string | null;
  status: string | null;
  severity: Severity;
  message: string | null;
  bytes_out: number;
  bytes_in: number;
  metadata: Record<string, unknown>;
}

export interface Alert {
  alert_id: string;
  rule_id: string;
  detection_kind: "rule" | "anomaly" | "ml";
  title: string;
  description: string;
  severity: Severity;
  confidence: number;
  status: AlertStatus;
  first_seen: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
  source_ip: string | null;
  affected_host: string | null;
  event_count: number;
  involved_users: string[];
  involved_hosts: string[];
  evidence: { event_id: string; timestamp: string; summary: string }[];
  recommended_action: string;
  correlation_key: string;
  anomaly_score: number | null;
  metadata: Record<string, unknown>;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface DashboardMetrics {
  generated_at: string;
  events_per_second: number;
  events_last_hour: number;
  events_last_24h: number;
  last_minute: Record<string, number>;
  active_alerts_total: number;
  active_alerts_by_severity: Record<Severity, number>;
  critical_alerts: number;
  high_alerts: number;
  resolved_alerts: number;
  false_positive_alerts: number;
  total_alerts: number;
  detection_rate: number;
  false_positive_rate: number;
}

export interface DetectionRule {
  rule_id: string;
  name: string;
  category: string;
  default_severity: Severity;
  kind: string;
  enabled: boolean;
  description: string;
  parameters: Record<string, unknown>;
  mitre_attack: string[];
  recommended_action: string;
}

export interface SystemStatus {
  status: string;
  version: string;
  env: string;
  uptime_seconds: number;
  generated_at: string;
  broker: Record<string, string>;
  feature_flags: Record<string, unknown>;
  components: Record<string, Record<string, unknown>>;
}

export interface SimulatorStatus {
  desired: {
    running: boolean;
    rate: number;
    scenario: string;
    attack_ratio: number;
    burst: boolean;
  };
  simulator_connected: boolean;
  last_heartbeat: unknown;
  stats: Record<string, unknown>;
}

export interface TopIp {
  source_ip: string;
  event_count: number;
  auth_failures: number;
  enrichment: {
    country: string | null;
    asn: string | null;
    category: string | null;
    reputation: string;
    reputation_score: number;
    is_private: boolean;
  };
}
