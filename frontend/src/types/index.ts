export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type AlertStatus =
  | "open"
  | "acknowledged"
  | "investigating"
  | "resolved"
  | "false_positive";
export type DetectionKind = "rule" | "anomaly" | "ml";

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

export interface AlertEvidence {
  event_id: string;
  timestamp: string;
  summary: string;
}

export interface Alert {
  alert_id: string;
  rule_id: string;
  detection_kind: DetectionKind;
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
  evidence: AlertEvidence[];
  recommended_action: string;
  correlation_key: string;
  anomaly_score: number | null;
  metadata: Record<string, unknown> & {
    status_history?: { from: string; to: string; at: string; by: string }[];
  };
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface DashboardMetrics {
  generated_at: string;
  worker_online: boolean;
  events_per_second: number | null;
  events_processed_per_second: number | null;
  pipeline_latency_ms: number | null;
  detection_latency_ms: number | null;
  alerts_per_minute: number | null;
  pipeline_health_pct: number | null;
  invalid_events_window: number | null;
  duplicate_events_window: number | null;
  consumer_lag: number | null;
  events_last_hour: number;
  events_last_24h: number;
  last_minute: Record<string, number>;
  active_alerts_total: number;
  active_alerts_by_severity: Record<Severity, number>;
  critical_alerts: number;
  high_alerts: number;
  acknowledged_alerts: number;
  investigating_alerts: number;
  resolved_alerts: number;
  false_positive_alerts: number;
  total_alerts: number;
  detection_rate: number;
  false_positive_rate: number;
}

export interface DetectionRule {
  rule_id: string;
  handle: string;
  name: string;
  category: string;
  default_severity: Severity;
  kind: DetectionKind;
  enabled: boolean;
  description: string;
  parameters: Record<string, unknown>;
  mitre_attack: string[];
  recommended_action: string;
  trigger_count: number;
  active_count: number;
  last_triggered: string | null;
}

export interface Component {
  status: string;
  [k: string]: unknown;
}

export interface SystemStatus {
  status: string;
  version: string;
  env: string;
  uptime_seconds: number;
  generated_at: string;
  broker: Record<string, string>;
  feature_flags: Record<string, unknown>;
  components: Record<string, Component>;
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
  stats: Record<string, number | string>;
}

export interface Enrichment {
  country: string | null;
  asn: string | null;
  category: string | null;
  reputation: string;
  reputation_score: number;
  is_private: boolean;
}

export interface TopIp {
  source_ip: string;
  event_count: number;
  auth_failures: number;
  enrichment: Enrichment;
}

export interface AnomalyItem {
  alert_id: string;
  rule_id: string;
  metric: string | null;
  current_value: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  deviation_pct: number | null;
  severity: Severity;
  confidence: number;
  anomaly_score: number | null;
  status: AlertStatus;
  first_seen: string;
  last_seen: string;
  description: string;
  source_ip: string | null;
}

export interface Baseline {
  metric: string;
  mean: number;
  std: number;
  samples: number;
  ready: boolean;
}

export interface PerfSample {
  events_per_second: number;
  events_processed_per_second: number;
  pipeline_latency_ms: number;
  detection_latency_ms: number;
  alerts_per_minute: number;
  pipeline_health_pct: number;
  invalid_events_window: number;
  duplicate_events_window: number;
  updated_at: number;
}

export interface TimeBucket {
  bucket: string;
  count: number;
  [k: string]: string | number;
}
export interface SeverityBucket {
  bucket: string;
  severity: string;
  count: number;
  [k: string]: string | number;
}
