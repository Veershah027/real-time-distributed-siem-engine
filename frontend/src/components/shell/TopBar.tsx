import { useQuery, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import { ms, metric } from "@/lib/format";
import { Icon } from "@/components/ui/Icon";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { RANGES, setTimeRange, useTimeRange } from "@/hooks/useTimeRange";
import { CommandSearch } from "./CommandSearch";

function SystemPill() {
  const { conn } = useRealtime();
  const { data } = useQuery({
    queryKey: ["system-status"],
    queryFn: api.systemStatus,
    refetchInterval: 8000,
  });
  const status =
    conn === "offline" || conn === "reconnecting" ? "degraded" : (data?.status ?? "loading");
  const meta: Record<string, { label: string; color: string }> = {
    healthy: { label: "System Online", color: "var(--ok)" },
    degraded: { label: "System Degraded", color: "var(--warn)" },
    down: { label: "System Offline", color: "var(--down)" },
    loading: { label: "Connecting", color: "var(--idle)" },
  };
  const m = meta[status] ?? meta.loading;
  return (
    <div className="flex items-center gap-2 rounded-md border border-line-strong bg-elev px-2.5 py-1">
      <span
        className={cn("h-2 w-2 rounded-full", status === "healthy" && "pulse-dot")}
        style={{ background: m.color, boxShadow: `0 0 6px ${m.color}66` }}
      />
      <span className="text-[11px] font-semibold uppercase tracking-[0.05em]" style={{ color: m.color }}>
        {m.label}
      </span>
    </div>
  );
}

function Telemetry() {
  const { liveMetrics } = useRealtime();
  const { data } = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 5000 });

  const eps = liveMetrics?.events_per_second ?? data?.events_per_second ?? null;
  const lat = liveMetrics?.pipeline_latency_ms ?? data?.pipeline_latency_ms ?? null;
  const alerts = data?.active_alerts_total ?? null;

  const item = (label: string, value: string, tone?: string) => (
    <div className="flex items-baseline gap-1.5">
      <span className="text-2xs uppercase tracking-[0.05em] text-faint">{label}</span>
      <span className={cn("tnum text-[12.5px] font-semibold", tone)}>{value}</span>
    </div>
  );

  return (
    <div className="hidden items-center gap-4 lg:flex">
      {item("Events/sec", metric(eps, { digits: 0 }))}
      {item("Pipeline", ms(lat))}
      {item(
        "Alerts",
        alerts === null ? "—" : String(alerts),
        alerts && alerts > 0 ? "text-sev-high" : undefined,
      )}
    </div>
  );
}

export function TopBar({ onMenu }: { onMenu: () => void }) {
  const qc = useQueryClient();
  const range = useTimeRange();

  return (
    <header
      className="flex shrink-0 items-center gap-3 border-b border-line bg-bg px-3"
      style={{ height: "var(--topbar-h)" }}
    >
      <button
        className="btn-ghost inline-flex h-8 w-8 items-center justify-center rounded text-dim md:hidden"
        onClick={onMenu}
        aria-label="Open navigation"
      >
        <Icon.menu size={17} />
      </button>

      <div className="hidden items-center gap-2 sm:flex">
        <span className="text-[13px] font-semibold uppercase tracking-[0.1em] text-ink">
          SIEM Command Center
        </span>
      </div>

      <div className="mx-1 hidden h-4 w-px bg-line-strong lg:block" />
      <Telemetry />

      <div className="flex-1" />

      <CommandSearch />

      <div className="inline-flex rounded-md border border-line-strong bg-elev p-0.5">
        {RANGES.map((r) => (
          <button
            key={r.label}
            onClick={() => setTimeRange(r)}
            className={cn(
              "rounded-[4px] px-2 py-1 text-[11px] font-medium tnum transition-colors",
              range.minutes === r.minutes ? "bg-panel-3 text-ink" : "text-faint hover:text-dim",
            )}
          >
            {r.label}
          </button>
        ))}
      </div>

      <button
        className="btn-ghost inline-flex h-8 w-8 items-center justify-center rounded text-dim hover:text-ink"
        onClick={() => qc.invalidateQueries()}
        title="Refresh all"
        aria-label="Refresh"
      >
        <Icon.refresh size={15} />
      </button>

      <SystemPill />
    </header>
  );
}
