import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ms, metric } from "@/lib/format";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, StatCard } from "@/components/ui/primitives";
import { MultiLine } from "@/components/charts";

export function Performance() {
  const rt = useRealtime();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["performance"],
    queryFn: api.performance,
    refetchInterval: 5000,
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState error={error} retry={() => refetch()} />;

  const cur = data!.current;
  const live = rt.liveMetrics ?? {};
  const val = (k: string): number | null => {
    const v = (live as Record<string, number>)[k] ?? cur[k];
    return typeof v === "number" ? v : null;
  };

  const history = data!.history.map((s) => ({
    t: new Date(s.updated_at * 1000).toISOString(),
    eps: s.events_per_second,
    pps: s.events_processed_per_second,
    pipeline: s.pipeline_latency_ms,
    detection: s.detection_latency_ms,
    alerts: s.alerts_per_minute,
  }));

  return (
    <div className="space-y-4">
      <PageHeader
        title="Pipeline Performance"
        subtitle="Measured by the stream processor. Figures depend on hardware and Docker configuration — nothing is projected."
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Events / sec" value={metric(val("events_per_second"), { digits: 0 })} sub="ingested" />
        <StatCard label="Processed / sec" value={metric(val("events_processed_per_second"), { digits: 0 })} sub="to PostgreSQL" />
        <StatCard label="Pipeline latency" value={ms(val("pipeline_latency_ms"))} sub="consume → persisted" />
        <StatCard label="Detection latency" value={ms(val("detection_latency_ms"))} sub="7 rules / event" />
        <StatCard label="Alerts / min" value={metric(val("alerts_per_minute"))} />
        <StatCard
          label="Consumer lag"
          value={data!.consumer_lag == null ? "—" : data!.consumer_lag.toLocaleString()}
          tone={data!.consumer_lag && data!.consumer_lag > 5000 ? "warn" : "ok"}
          sub="unconsumed messages"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Pipeline health"
          value={val("pipeline_health_pct") == null ? "—" : `${(val("pipeline_health_pct") as number).toFixed(1)}%`}
          tone="ok"
          sub="1 − reject rate"
        />
        <StatCard label="Invalid (5s window)" value={metric(val("invalid_events_window"), { digits: 0 })} />
        <StatCard label="Duplicates (5s window)" value={metric(val("duplicate_events_window"), { digits: 0 })} />
        <StatCard label="Samples buffered" value={data!.samples} sub="~5s each" />
      </div>

      <Panel title="Throughput — events/sec vs processed/sec" className="h-60">
        <div className="h-full p-1">
          <MultiLine
            data={history}
            series={[
              { key: "eps", label: "Ingested/sec", color: "var(--accent)" },
              { key: "pps", label: "Processed/sec", color: "var(--ok)" },
            ]}
          />
        </div>
      </Panel>

      <div className="grid gap-3 xl:grid-cols-2">
        <Panel title="Latency (ms/event)" className="h-56">
          <div className="h-full p-1">
            <MultiLine
              data={history}
              series={[
                { key: "pipeline", label: "Pipeline", color: "var(--sev-medium)" },
                { key: "detection", label: "Detection", color: "#8b5cf6" },
              ]}
            />
          </div>
        </Panel>
        <Panel title="Alerts / minute" className="h-56">
          <div className="h-full p-1">
            <MultiLine
              data={history}
              series={[{ key: "alerts", label: "Alerts/min", color: "var(--sev-high)" }]}
            />
          </div>
        </Panel>
      </div>

      <p className="text-2xs text-faint">
        The <span className="font-mono">benchmarks/throughput.py</span> script produces a full
        report against a running stack.
      </p>
    </div>
  );
}
