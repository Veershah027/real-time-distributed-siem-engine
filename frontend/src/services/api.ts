import type {
  Alert,
  AlertStatus,
  DashboardMetrics,
  DetectionRule,
  Page,
  SecurityEvent,
  SimulatorStatus,
  SystemStatus,
  TopIp,
} from "@/types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}: ${detail}`);
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

export const api = {
  health: () => req<{ status: string; version: string }>("/health"),
  metrics: () => req<DashboardMetrics>("/api/metrics"),
  timeseries: (minutes = 60, bucket = 60) =>
    req<{
      window_minutes: number;
      events: { bucket: string; count: number }[];
      alerts: { bucket: string; severity: string; count: number }[];
    }>(`/api/metrics/timeseries${qs({ minutes, bucket_seconds: bucket })}`),

  events: (params: Record<string, unknown> = {}) =>
    req<Page<SecurityEvent>>(`/api/events${qs(params)}`),
  event: (id: string) => req<SecurityEvent>(`/api/events/${id}`),

  alerts: (params: Record<string, unknown> = {}) =>
    req<Page<Alert>>(`/api/alerts${qs(params)}`),
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

  detections: () => req<{ rules: DetectionRule[]; count: number }>("/api/detections"),
  topIps: (minutes = 60, limit = 10) =>
    req<{ window_minutes: number; items: TopIp[] }>(
      `/api/threats/top-ips${qs({ minutes, limit })}`,
    ),
  eventTypes: (minutes = 60) =>
    req<{ items: { event_type: string; count: number }[] }>(
      `/api/threats/event-types${qs({ minutes })}`,
    ),

  systemStatus: () => req<SystemStatus>("/api/system/status"),

  simulatorStatus: () => req<SimulatorStatus>("/api/simulator/status"),
  simulatorScenarios: () => req<{ scenarios: string[] }>("/api/simulator/scenarios"),
  simulatorStart: (cfg: Record<string, unknown>) =>
    req<{ ok: boolean }>("/api/simulator/start", {
      method: "POST",
      body: JSON.stringify(cfg),
    }),
  simulatorStop: () => req<{ ok: boolean }>("/api/simulator/stop", { method: "POST" }),
  simulatorConfigure: (cfg: Record<string, unknown>) =>
    req<{ ok: boolean }>("/api/simulator/configure", {
      method: "POST",
      body: JSON.stringify(cfg),
    }),
};
