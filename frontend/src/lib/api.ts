import type {
  Alert,
  AlertStatus,
  AnomalyItem,
  Baseline,
  DashboardMetrics,
  DetectionRule,
  Page,
  PerfSample,
  SecurityEvent,
  SeverityBucket,
  SimulatorStatus,
  SystemStatus,
  TimeBucket,
  TopIp,
} from "@/types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    });
  } catch {
    throw new ApiError(0, "network unreachable");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const qs = (params: Record<string, unknown>) => {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
};

export interface ThreatActivity {
  window_minutes: number;
  events_timeseries: TimeBucket[];
  alerts_timeseries: SeverityBucket[];
  event_severity: { severity: string; count: number }[];
  event_types: { event_type: string; count: number }[];
  rule_frequency: { rule_id: string; trigger_count: number; last_triggered: string | null }[];
  top_source_ips: TopIp[];
  top_attacked_hosts: {
    host: string;
    alert_count: number;
    event_count: number;
    critical_alerts: number;
  }[];
  top_event_sources: {
    host: string;
    source_type: string;
    event_count: number;
    high_severity_events: number;
  }[];
}

export const api = {
  health: () => req<{ status: string; version: string }>("/health"),
  ready: () =>
    req<{ status: string; version: string; checks: Record<string, string> }>("/health/ready"),

  metrics: () => req<DashboardMetrics>("/api/metrics"),
  timeseries: (minutes = 60, bucket = 60) =>
    req<{ window_minutes: number; events: TimeBucket[]; alerts: SeverityBucket[] }>(
      `/api/metrics/timeseries${qs({ minutes, bucket_seconds: bucket })}`,
    ),

  events: (params: Record<string, unknown> = {}) =>
    req<Page<SecurityEvent>>(`/api/events${qs(params)}`),
  event: (id: string) => req<SecurityEvent>(`/api/events/${id}`),

  alerts: (params: Record<string, unknown> = {}) => req<Page<Alert>>(`/api/alerts${qs(params)}`),
  alert: (id: string) => req<Alert>(`/api/alerts/${id}`),
  alertEvents: (id: string) =>
    req<{ alert_id: string; count: number; events: SecurityEvent[] }>(
      `/api/alerts/${id}/events`,
    ),
  updateAlert: (id: string, status: AlertStatus, note?: string) =>
    req<Alert>(`/api/alerts/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    }),

  detections: () =>
    req<{ rules: DetectionRule[]; count: number; total_triggers: number }>("/api/detections"),

  anomalies: (limit = 30) =>
    req<{
      z_score_threshold: number;
      min_samples: number;
      anomalies: AnomalyItem[];
      baselines: Baseline[];
    }>(`/api/anomalies${qs({ limit })}`),

  threatActivity: (minutes = 180, bucket = 300) =>
    req<ThreatActivity>(`/api/analytics/threat-activity${qs({ minutes, bucket_seconds: bucket })}`),
  heatmap: (hours = 24) =>
    req<{
      available: boolean;
      hours: number;
      severities: string[];
      cells: SeverityBucket[];
      total: number;
    }>(`/api/analytics/heatmap${qs({ hours })}`),
  performance: () =>
    req<{
      current: Record<string, number | null>;
      consumer_lag: number | null;
      history: PerfSample[];
      samples: number;
    }>("/api/analytics/performance"),

  topIps: (minutes = 60, limit = 10) =>
    req<{ window_minutes: number; items: TopIp[] }>(
      `/api/threats/top-ips${qs({ minutes, limit })}`,
    ),
  topHosts: (minutes = 60, limit = 10) =>
    req<TopHostsResponse>(`/api/threats/top-hosts${qs({ minutes, limit })}`),
  eventTypes: (minutes = 60) =>
    req<{ items: { event_type: string; count: number }[] }>(
      `/api/threats/event-types${qs({ minutes })}`,
    ),
  enrich: (ip: string) => req<TopIp["enrichment"]>(`/api/threats/enrich/${encodeURIComponent(ip)}`),

  systemStatus: () => req<SystemStatus>("/api/system/status"),

  simulatorStatus: () => req<SimulatorStatus>("/api/simulator/status"),
  simulatorScenarios: () => req<{ scenarios: string[] }>("/api/simulator/scenarios"),
  simulatorStart: (cfg: Record<string, unknown>) =>
    req<{ ok: boolean }>("/api/simulator/start", { method: "POST", body: JSON.stringify(cfg) }),
  simulatorStop: () => req<{ ok: boolean }>("/api/simulator/stop", { method: "POST" }),
  simulatorConfigure: (cfg: Record<string, unknown>) =>
    req<{ ok: boolean }>("/api/simulator/configure", { method: "POST", body: JSON.stringify(cfg) }),
};

export interface TopHostsResponse {
  window_minutes: number;
  top_event_sources: ThreatActivity["top_event_sources"];
  top_attacked_hosts: ThreatActivity["top_attacked_hosts"];
}
