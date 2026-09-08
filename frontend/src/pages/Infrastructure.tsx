import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import { ms } from "@/lib/format";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState } from "@/components/ui/primitives";
import { StatusDot } from "@/components/ui/badges";

const PIPELINE = [
  { key: "Event Producers", comp: "simulator", note: "synthetic log generator" },
  { key: "Redpanda (broker)", comp: "redpanda", note: "Kafka-compatible event log" },
  { key: "Stream Processor", comp: "stream_processor", note: "validate → detect → persist" },
  { key: "PostgreSQL", comp: "postgres", note: "durable events + alerts + audit" },
  { key: "Redis", comp: "redis", note: "sliding windows + pub/sub" },
  { key: "FastAPI", comp: "api", note: "REST + WebSocket" },
  { key: "SOC Console", comp: "frontend", note: "this interface" },
];

function state(status?: string): "up" | "down" | "idle" | "unknown" {
  if (status === "up") return "up";
  if (status === "down") return "down";
  if (status === "idle") return "idle";
  return "unknown";
}

export function Infrastructure() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["system-status"],
    queryFn: api.systemStatus,
    refetchInterval: 5000,
  });

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState error={error} retry={() => refetch()} />;
  const s = data!;
  const c = s.components;
  const sp = c.stream_processor ?? {};

  return (
    <div className="space-y-4">
      <PageHeader
        title="Infrastructure"
        subtitle={`Distributed pipeline · overall status: ${s.status} · uptime ${Math.floor(s.uptime_seconds / 60)}m`}
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Panel title="Event Pipeline">
          <div className="flex flex-col gap-1.5 p-4">
            {PIPELINE.map((stage, i) => {
              const st = state((c[stage.comp] as { status?: string })?.status);
              return (
                <div key={stage.key}>
                  <div
                    className={cn(
                      "flex items-center gap-3 rounded-md border px-3 py-2.5",
                      st === "up"
                        ? "border-ok/30 bg-ok/5"
                        : st === "down"
                          ? "border-down/40 bg-down/8"
                          : "border-line bg-elev",
                    )}
                  >
                    <StatusDot state={st} pulse />
                    <div className="min-w-0">
                      <div className="text-[12.5px] font-medium text-ink">{stage.key}</div>
                      <div className="text-2xs text-faint">{stage.note}</div>
                    </div>
                    <span className="ml-auto font-mono text-2xs uppercase text-faint">{st}</span>
                  </div>
                  {i < PIPELINE.length - 1 && (
                    <div className="flex justify-center py-0.5 text-line-strong">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 5v14M6 13l6 6 6-6" />
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>

        <div className="space-y-4">
          <Panel title="Component Health">
            <div className="divide-y divide-line">
              {Object.entries(c).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between px-3 py-2">
                  <div>
                    <div className="text-[12px] font-medium capitalize text-ink">
                      {name.replace(/_/g, " ")}
                    </div>
                    <div className="text-2xs text-faint">
                      {"latency_ms" in info
                        ? `${info.latency_ms} ms`
                        : "endpoint" in info
                          ? String(info.endpoint)
                          : ""}
                    </div>
                  </div>
                  <StatusDot state={state(info.status as string)} label={String(info.status)} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Message Broker">
            <dl className="divide-y divide-line text-[12px]">
              {Object.entries(s.broker).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3 px-3 py-1.5">
                  <dt className="shrink-0 text-faint">{k.replace(/_/g, " ")}</dt>
                  <dd className="truncate font-mono text-2xs text-dim">{v}</dd>
                </div>
              ))}
              <div className="flex justify-between px-3 py-1.5">
                <dt className="text-faint">consumer lag</dt>
                <dd className="font-mono text-2xs text-dim">
                  {sp.consumer_lag == null ? "—" : Number(sp.consumer_lag).toLocaleString()}
                </dd>
              </div>
            </dl>
          </Panel>

          <Panel title="Stream Processor Vitals">
            <dl className="divide-y divide-line text-[12px]">
              {(
                [
                  ["events/sec", sp.events_per_second],
                  ["processed/sec", sp.events_processed_per_second],
                  [
                    "pipeline latency",
                    sp.pipeline_latency_ms != null ? ms(Number(sp.pipeline_latency_ms)) : "—",
                  ],
                  [
                    "detection latency",
                    sp.detection_latency_ms != null ? ms(Number(sp.detection_latency_ms)) : "—",
                  ],
                  [
                    "health",
                    sp.pipeline_health_pct != null
                      ? `${Number(sp.pipeline_health_pct).toFixed(1)}%`
                      : "—",
                  ],
                ] as [string, unknown][]
              ).map(([k, v]) => (
                <div key={k} className="flex justify-between px-3 py-1.5">
                  <dt className="text-faint">{k}</dt>
                  <dd className="tnum text-dim">{v == null ? "—" : String(v)}</dd>
                </div>
              ))}
            </dl>
          </Panel>
        </div>
      </div>
    </div>
  );
}
