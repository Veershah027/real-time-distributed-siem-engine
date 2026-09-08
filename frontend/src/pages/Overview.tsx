import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { compactNum, metric, ms, num } from "@/lib/format";
import { SEVERITY_META, SEVERITY_ORDER } from "@/lib/severity";
import { bucketFor, useTimeRange } from "@/hooks/useTimeRange";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, StatCard } from "@/components/ui/primitives";
import { Donut, HBar, SeverityStackedBar, TimeSeriesArea } from "@/components/charts";
import { EventStream } from "@/components/events/EventStream";
import { AlertQueue } from "@/components/alerts/AlertQueue";
import { AlertInvestigation } from "@/components/alerts/AlertInvestigation";

export function Overview() {
  const navigate = useNavigate();
  const range = useTimeRange();
  const rt = useRealtime();
  const [selected, setSelected] = useState<string | null>(null);

  const metricsQ = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 5000 });
  const seriesQ = useQuery({
    queryKey: ["timeseries", range.minutes],
    queryFn: () => api.timeseries(range.minutes, bucketFor(range.minutes)),
    refetchInterval: 15000,
  });
  const topIpsQ = useQuery({
    queryKey: ["top-ips", range.minutes],
    queryFn: () => api.topIps(range.minutes, 6),
    refetchInterval: 20000,
  });

  const m = metricsQ.data;
  const liveEps = rt.liveMetrics?.events_per_second ?? m?.events_per_second ?? null;

  const alertBuckets = useMemo(() => {
    const rows = seriesQ.data?.alerts ?? [];
    const map = new Map<string, Record<string, number>>();
    for (const r of rows) {
      const b = map.get(r.bucket) ?? {};
      b[r.severity] = (b[r.severity] ?? 0) + r.count;
      map.set(r.bucket, b);
    }
    return [...map.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([bucket, sev]) => ({ bucket, ...sev }));
  }, [seriesQ.data]);

  const sevDonut = SEVERITY_ORDER.map((s) => ({
    name: SEVERITY_META[s].label,
    value: m?.active_alerts_by_severity[s] ?? 0,
    color: SEVERITY_META[s].color,
  }));

  const health = m?.pipeline_health_pct;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Security Overview"
        subtitle={`Real-time monitoring · ${m?.worker_online ? "stream processor online" : "stream processor offline"}`}
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="Events (24h)"
          value={m ? compactNum(m.events_last_24h) : "—"}
          sub={m ? `${compactNum(m.events_last_hour)} in last hour` : undefined}
        />
        <StatCard label="Events / sec" value={metric(liveEps, { digits: 0 })} sub="ingested, measured" />
        <StatCard
          label="Active Alerts"
          value={m?.active_alerts_total ?? "—"}
          sub={m ? `${m.investigating_alerts} investigating` : undefined}
        />
        <StatCard label="High Severity" value={m?.high_alerts ?? "—"} tone="high" />
        <StatCard label="Critical" value={m?.critical_alerts ?? "—"} tone="critical" />
        <StatCard
          label="Pipeline Health"
          value={health == null ? "—" : `${health.toFixed(1)}%`}
          tone={health == null ? "default" : health >= 99 ? "ok" : health >= 90 ? "warn" : "critical"}
          sub={m ? `${ms(m.pipeline_latency_ms)} latency` : undefined}
        />
      </div>

      <Panel
        title="Live Security Events"
        className="h-[360px]"
        actions={
          <button className="btn btn-xs btn-ghost" onClick={() => navigate("/events")}>
            Open explorer
          </button>
        }
      >
        <EventStream
          events={rt.events.slice(0, 60)}
          paused={rt.paused}
          onPause={rt.setPaused}
          liveCount={rt.eventCount}
        />
      </Panel>

      <div className="grid gap-3 xl:grid-cols-3">
        <Panel title="Events over time" className="h-56 xl:col-span-2">
          <div className="h-full p-1">
            <TimeSeriesArea data={seriesQ.data?.events ?? []} />
          </div>
        </Panel>
        <Panel title="Active alerts by severity" className="h-56">
          <div className="h-full p-1">
            <Donut data={sevDonut} />
          </div>
        </Panel>
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        <Panel
          title="Active Alerts"
          className="xl:col-span-2"
          bodyClassName="max-h-[380px] overflow-auto"
          actions={
            <button className="btn btn-xs btn-ghost" onClick={() => navigate("/alerts")}>
              All alerts
            </button>
          }
        >
          <AlertQueue alerts={rt.alerts} onSelect={setSelected} flashFirst />
        </Panel>
        <div className="space-y-3">
          <Panel title="Alerts over time" className="h-44">
            <div className="h-full p-1">
              <SeverityStackedBar data={alertBuckets} />
            </div>
          </Panel>
          <Panel title="Top source IPs" bodyClassName="max-h-52 overflow-auto">
            <HBar
              data={(topIpsQ.data?.items ?? []).map((t) => ({
                name: t.source_ip,
                value: t.event_count,
                sub: t.auth_failures > 0 ? `${num(t.auth_failures)} auth fails` : undefined,
              }))}
              onClick={(ip) => navigate(`/events?source_ip=${ip}`)}
            />
          </Panel>
        </div>
      </div>

      {selected && <AlertInvestigation alertId={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
