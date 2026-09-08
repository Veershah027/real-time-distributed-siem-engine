import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useRealtimeContext } from "@/hooks/realtimeContext";
import { StatCard, Card } from "@/components/primitives";
import { EventTable } from "@/components/EventTable";
import { AlertFeed } from "@/components/AlertFeed";
import { AlertDetail } from "@/components/AlertDetail";
import {
  AlertsBarChart,
  DistributionPie,
  EventsAreaChart,
  HBarChart,
  SEV_COLORS,
} from "@/components/charts";
import { compactNum, pct } from "@/lib/format";

const SEV_ORDER = ["critical", "high", "medium", "low", "info"] as const;

export function Dashboard() {
  const { events, alerts, eps, connected } = useRealtimeContext();
  const [selected, setSelected] = useState<string | null>(null);

  const metrics = useQuery({
    queryKey: ["metrics"],
    queryFn: api.metrics,
    refetchInterval: 5000,
  });
  const series = useQuery({
    queryKey: ["timeseries", 60],
    queryFn: () => api.timeseries(60, 60),
    refetchInterval: 15000,
  });
  const topIps = useQuery({
    queryKey: ["top-ips", 60],
    queryFn: () => api.topIps(60, 8),
    refetchInterval: 15000,
  });
  const eventTypes = useQuery({
    queryKey: ["event-types", 60],
    queryFn: () => api.eventTypes(60),
    refetchInterval: 20000,
  });

  const m = metrics.data;
  const liveEps = eps ?? m?.events_per_second ?? 0;

  const alertBuckets = useMemo(() => {
    const rows = series.data?.alerts ?? [];
    const map = new Map<string, Record<string, number>>();
    for (const r of rows) {
      const b = map.get(r.bucket) ?? {};
      b[r.severity] = (b[r.severity] ?? 0) + r.count;
      map.set(r.bucket, b);
    }
    return [...map.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([bucket, sev]) => ({ bucket, ...sev }));
  }, [series.data]);

  const sevDistribution = useMemo(() => {
    const src: Partial<Record<string, number>> = m?.active_alerts_by_severity ?? {};
    return SEV_ORDER.map((s) => ({
      name: s,
      value: src[s] ?? 0,
      color: SEV_COLORS[s],
    }));
  }, [m]);

  const health = m
    ? m.critical_alerts > 0
      ? { label: "Critical", tone: "critical" as const }
      : m.high_alerts > 0
        ? { label: "Elevated", tone: "high" as const }
        : { label: "Nominal", tone: "good" as const }
    : { label: "—", tone: "default" as const };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-7">
        <StatCard
          label="Events / sec"
          value={liveEps.toFixed(1)}
          sub={connected ? "live" : "stale"}
        />
        <StatCard
          label="Events (24h)"
          value={m ? compactNum(m.events_last_24h) : "—"}
          sub={m ? `${compactNum(m.events_last_hour)} last hour` : undefined}
        />
        <StatCard label="Active alerts" value={m?.active_alerts_total ?? "—"} />
        <StatCard label="Critical" value={m?.critical_alerts ?? "—"} tone="critical" />
        <StatCard label="High" value={m?.high_alerts ?? "—"} tone="high" />
        <StatCard
          label="Detection rate"
          value={m ? pct(m.detection_rate) : "—"}
          sub="alerts / events (24h)"
        />
        <StatCard label="System health" value={health.label} tone={health.tone} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card title="Events over time (60m)" className="h-64 xl:col-span-2">
          <div className="h-full p-2">
            <EventsAreaChart data={series.data?.events ?? []} />
          </div>
        </Card>
        <Card title="Active alerts by severity" className="h-64">
          <div className="h-full p-2">
            <DistributionPie data={sevDistribution} />
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card title="Alerts over time (60m)" className="h-64 xl:col-span-2">
          <div className="h-full p-2">
            <AlertsBarChart data={alertBuckets} />
          </div>
        </Card>
        <Card title="Top source IPs (60m)" className="h-64">
          <div className="h-full p-2">
            <HBarChart
              data={(topIps.data?.items ?? []).map((t) => ({
                name: t.source_ip,
                value: t.event_count,
              }))}
            />
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card
          title="Live event stream"
          className="xl:col-span-2"
          action={<span className="text-[11px] text-slate-500">{events.length} buffered</span>}
        >
          <div className="max-h-[26rem] overflow-auto">
            <EventTable events={events.slice(0, 40)} highlightNew />
          </div>
        </Card>
        <Card
          title="Alert feed"
          action={<span className="text-[11px] text-slate-500">{alerts.length} recent</span>}
        >
          <div className="max-h-[26rem] overflow-auto">
            <AlertFeed alerts={alerts} onSelect={setSelected} highlightNew />
          </div>
        </Card>
      </div>

      <Card title="Event types (60m)" className="h-56">
        <div className="h-full p-2">
          <HBarChart
            data={(eventTypes.data?.items ?? []).slice(0, 10).map((t) => ({
              name: t.event_type,
              value: t.count,
            }))}
            color="#a78bfa"
          />
        </div>
      </Card>

      {selected && <AlertDetail alertId={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
