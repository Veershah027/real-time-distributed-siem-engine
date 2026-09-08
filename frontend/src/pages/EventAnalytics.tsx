import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { compactNum } from "@/lib/format";
import { eventTypeLabel } from "@/lib/severity";
import { bucketFor, useTimeRange } from "@/hooks/useTimeRange";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, StatCard } from "@/components/ui/primitives";
import { HBar, TimeSeriesArea } from "@/components/charts";

export function EventAnalytics() {
  const navigate = useNavigate();
  const range = useTimeRange();
  const metricsQ = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 5000 });
  const taQ = useQuery({
    queryKey: ["threat-activity", range.minutes],
    queryFn: () => api.threatActivity(range.minutes, bucketFor(range.minutes)),
    refetchInterval: 15000,
  });

  if (taQ.isLoading) return <Loading />;
  if (taQ.isError) return <ErrorState error={taQ.error} retry={() => taQ.refetch()} />;
  const d = taQ.data!;
  const m = metricsQ.data;
  const totalEvents = d.events_timeseries.reduce((s, b) => s + b.count, 0);
  const lm = m?.last_minute ?? {};

  return (
    <div className="space-y-4">
      <PageHeader title="Event Analytics" subtitle={`Ingestion breakdown over the last ${range.label}`} />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label={`Events (${range.label})`} value={compactNum(totalEvents)} />
        <StatCard label="Events / min (last)" value={lm.events_per_min ?? "—"} />
        <StatCard label="Auth failures / min" value={lm.auth_failures_per_min ?? "—"} tone="high" />
        <StatCard label="Unique source IPs / min" value={lm.unique_source_ips ?? "—"} />
      </div>

      <Panel title="Event volume over time" className="h-64">
        <div className="h-full p-1">
          <TimeSeriesArea data={d.events_timeseries} />
        </div>
      </Panel>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Event types" bodyClassName="max-h-96 overflow-auto">
          <HBar
            data={d.event_types.map((t) => ({ name: eventTypeLabel(t.event_type), value: t.count }))}
            color="#8b5cf6"
          />
        </Panel>
        <Panel title="Top event-producing hosts" bodyClassName="max-h-96 overflow-auto">
          <HBar
            data={d.top_event_sources.map((h) => ({
              name: h.host,
              value: h.event_count,
              sub: `${h.source_type}${h.high_severity_events ? ` · ${h.high_severity_events} high-sev` : ""}`,
            }))}
            onClick={(host) => navigate(`/events?source=${encodeURIComponent(host)}`)}
          />
        </Panel>
      </div>
    </div>
  );
}
