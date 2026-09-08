import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import { fullTime, relTime, signedPct } from "@/lib/format";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, StatCard, EmptyState } from "@/components/ui/primitives";
import { SeverityBadge } from "@/components/ui/badges";
import { AlertInvestigation } from "@/components/alerts/AlertInvestigation";
import { Icon } from "@/components/ui/Icon";

const METRIC_LABEL: Record<string, string> = {
  events_per_min: "Events / min",
  auth_failures_per_min: "Auth failures / min",
  unique_source_ips: "Unique source IPs / min",
  outbound_mib_per_min: "Outbound MiB / min",
  db_errors_per_min: "DB errors / min",
  firewall_denies_per_min: "Firewall denies / min",
};

export function Anomalies() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => api.anomalies(40),
    refetchInterval: 10000,
  });
  const [selected, setSelected] = useState<string | null>(null);

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState error={error} retry={() => refetch()} />;

  const { anomalies, baselines, z_score_threshold, min_samples } = data!;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Anomaly Detection"
        subtitle={`EWMA z-score baseline · threshold ${z_score_threshold}σ · ${min_samples} min samples · not a production IDS`}
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Anomalies Flagged" value={anomalies.length} tone={anomalies.length ? "high" : "default"} />
        <StatCard
          label="Baselines Ready"
          value={`${baselines.filter((b) => b.ready).length}/${baselines.length}`}
        />
        <StatCard
          label="Z-Score Threshold"
          value={`${z_score_threshold}σ`}
        />
        <StatCard
          label="Latest Deviation"
          value={anomalies[0] ? signedPct(anomalies[0].deviation_pct) : "—"}
          tone={anomalies[0] && (anomalies[0].deviation_pct ?? 0) > 0 ? "high" : "default"}
        />
      </div>

      <Panel title="Rolling Baselines (live EWMA state)">
        <div className="grid gap-px bg-line sm:grid-cols-2 lg:grid-cols-3">
          {baselines.map((b) => (
            <div key={b.metric} className="bg-panel p-3">
              <div className="flex items-center justify-between">
                <span className="text-[11.5px] font-medium text-dim">
                  {METRIC_LABEL[b.metric] ?? b.metric}
                </span>
                <span
                  className={cn(
                    "chip",
                    b.ready ? "bg-ok/12 text-ok" : "bg-idle/12 text-idle",
                  )}
                >
                  {b.ready ? "ready" : `${b.samples}/${min_samples}`}
                </span>
              </div>
              <div className="mt-1.5 font-mono text-[13px] tnum text-ink">
                μ {b.mean.toLocaleString()}{" "}
                <span className="text-faint">± {b.std.toLocaleString()}</span>
              </div>
              <div className="mt-0.5 text-2xs text-faint">{b.samples.toLocaleString()} samples observed</div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Flagged Anomalies">
        {anomalies.length === 0 ? (
          <EmptyState
            title="No anomalies flagged"
            hint="An anomaly is raised when a per-minute metric deviates beyond the z-score threshold from its baseline. Run a burst or attack scenario to generate one."
            icon={<Icon.anomaly size={22} />}
          />
        ) : (
          <ul className="divide-y divide-line">
            {anomalies.map((a) => (
              <li
                key={a.alert_id}
                onClick={() => setSelected(a.alert_id)}
                className="cursor-pointer px-3 py-2.5 hover:bg-panel-2"
              >
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={a.severity} />
                  <span className="text-[12.5px] font-medium text-ink">
                    {METRIC_LABEL[a.metric ?? ""] ?? a.metric ?? a.rule_id}
                  </span>
                  <span className="ml-auto text-2xs text-faint" title={fullTime(a.last_seen)}>
                    {relTime(a.last_seen)}
                  </span>
                </div>
                <div className="mt-1.5 grid grid-cols-2 gap-x-6 gap-y-1 font-mono text-[11px] sm:grid-cols-4">
                  <span>
                    <span className="text-faint">current </span>
                    <span className="text-ink">{a.current_value.toLocaleString()}</span>
                  </span>
                  <span>
                    <span className="text-faint">baseline </span>
                    <span className="text-dim">
                      {a.baseline_mean.toLocaleString()} ± {a.baseline_std.toLocaleString()}
                    </span>
                  </span>
                  <span>
                    <span className="text-faint">deviation </span>
                    <span
                      className={
                        (a.deviation_pct ?? 0) > 0 ? "text-sev-high" : "text-sev-low"
                      }
                    >
                      {signedPct(a.deviation_pct)}
                    </span>
                  </span>
                  <span>
                    <span className="text-faint">z-score </span>
                    <span className="text-ink">{a.z_score.toFixed(1)}σ</span>
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {selected && <AlertInvestigation alertId={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
