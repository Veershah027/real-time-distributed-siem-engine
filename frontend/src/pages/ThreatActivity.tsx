import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { SEVERITY_META, SEVERITY_ORDER } from "@/lib/severity";
import { bucketFor, useTimeRange } from "@/hooks/useTimeRange";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, EmptyState } from "@/components/ui/primitives";
import { Donut, HBar, Heatmap, SeverityStackedBar, TimeSeriesArea } from "@/components/charts";
import { eventTypeLabel } from "@/lib/severity";

export function ThreatActivity() {
  const navigate = useNavigate();
  const range = useTimeRange();

  const q = useQuery({
    queryKey: ["threat-activity", range.minutes],
    queryFn: () => api.threatActivity(range.minutes, bucketFor(range.minutes)),
    refetchInterval: 15000,
  });
  const heatQ = useQuery({
    queryKey: ["heatmap"],
    queryFn: () => api.heatmap(24),
    refetchInterval: 60000,
  });

  const d = q.data;

  const alertBuckets = useMemo(() => {
    const map = new Map<string, Record<string, number>>();
    for (const r of d?.alerts_timeseries ?? []) {
      const b = map.get(r.bucket) ?? {};
      b[r.severity] = (b[r.severity] ?? 0) + r.count;
      map.set(r.bucket, b);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([bucket, s]) => ({ bucket, ...s }));
  }, [d]);

  const heatBuckets = useMemo(() => {
    const set = new Set<string>();
    for (const c of heatQ.data?.cells ?? []) set.add(c.bucket);
    return [...set].sort();
  }, [heatQ.data]);

  if (q.isLoading) return <Loading />;
  if (q.isError) return <ErrorState error={q.error} retry={() => q.refetch()} />;

  const evSeverity = SEVERITY_ORDER.map((s) => ({
    name: SEVERITY_META[s].label,
    value: d!.event_severity.find((x) => x.severity === s)?.count ?? 0,
    color: SEVERITY_META[s].color,
  }));

  return (
    <div className="space-y-4">
      <PageHeader
        title="Threat Activity"
        subtitle={`Attack and detection analytics over the last ${range.label}`}
      />

      <div className="grid gap-3 xl:grid-cols-2">
        <Panel title="Events over time" className="h-52">
          <div className="h-full p-1">
            <TimeSeriesArea data={d!.events_timeseries} />
          </div>
        </Panel>
        <Panel title="Alerts over time (by severity)" className="h-52">
          <div className="h-full p-1">
            <SeverityStackedBar data={alertBuckets} />
          </div>
        </Panel>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <Panel title="Event severity distribution" className="h-56">
          <div className="h-full p-1">
            <Donut data={evSeverity} />
          </div>
        </Panel>
        <Panel title="Detection rule frequency" className="h-56" bodyClassName="overflow-auto">
          <HBar
            data={d!.rule_frequency
              .filter((r) => r.trigger_count > 0)
              .slice(0, 8)
              .map((r) => ({ name: r.rule_id, value: r.trigger_count }))}
            color="var(--sev-high)"
            onClick={(rid) => navigate(`/alerts?rule=${rid}`)}
          />
        </Panel>
        <Panel title="Event types" className="h-56" bodyClassName="overflow-auto">
          <HBar
            data={d!.event_types.slice(0, 8).map((t) => ({
              name: eventTypeLabel(t.event_type),
              value: t.count,
            }))}
            color="#8b5cf6"
          />
        </Panel>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Top source IPs" bodyClassName="max-h-72 overflow-auto">
          <HBar
            data={d!.top_source_ips.map((t) => ({
              name: t.source_ip,
              value: t.event_count,
              sub: `${t.enrichment.reputation}${t.auth_failures ? ` · ${num(t.auth_failures)} fails` : ""}`,
            }))}
            onClick={(ip) => navigate(`/events?source_ip=${ip}`)}
          />
        </Panel>
        <Panel title="Top attacked hosts" bodyClassName="max-h-72 overflow-auto">
          {d!.top_attacked_hosts.length === 0 ? (
            <EmptyState title="No alerts on hosts in this window" />
          ) : (
            <HBar
              data={d!.top_attacked_hosts.map((h) => ({
                name: h.host,
                value: h.alert_count,
                sub: `${h.event_count.toLocaleString()} events${h.critical_alerts ? ` · ${h.critical_alerts} critical` : ""}`,
              }))}
              color="var(--sev-critical)"
            />
          )}
        </Panel>
      </div>

      <Panel title="Security Heatmap — alert activity by hour × severity (24h)">
        {!heatQ.data?.available ? (
          <EmptyState
            title="Not enough alert data yet"
            hint="The heatmap renders once there is meaningful attack activity across the day."
          />
        ) : (
          <Heatmap
            buckets={heatBuckets}
            severities={heatQ.data.severities}
            cells={heatQ.data.cells}
          />
        )}
      </Panel>
    </div>
  );
}
