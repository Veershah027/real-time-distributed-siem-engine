import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState } from "@/components/ui/primitives";
import { StatusDot } from "@/components/ui/badges";

export function Settings() {
  const sysQ = useQuery({ queryKey: ["system-status"], queryFn: api.systemStatus });
  const rulesQ = useQuery({ queryKey: ["detections"], queryFn: api.detections });

  if (sysQ.isLoading) return <Loading />;
  if (sysQ.isError) return <ErrorState error={sysQ.error} retry={() => sysQ.refetch()} />;
  const s = sysQ.data!;

  return (
    <div className="max-w-3xl space-y-4">
      <PageHeader
        title="Settings"
        subtitle="Runtime configuration is environment-driven. This view is read-only."
      />

      <Panel title="Deployment">
        <dl className="divide-y divide-line text-[12.5px]">
          {[
            ["Version", s.version],
            ["Environment", s.env],
            ["Broker", `${s.broker.type} · ${s.broker.bootstrap_servers}`],
            ["Topic", s.broker.topic],
            ["Consumer group", s.broker.consumer_group],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-3 px-3 py-2">
              <dt className="text-faint">{k}</dt>
              <dd className="font-mono text-2xs text-dim">{v}</dd>
            </div>
          ))}
        </dl>
      </Panel>

      <Panel title="Feature Flags">
        <dl className="divide-y divide-line text-[12.5px]">
          {Object.entries(s.feature_flags).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between px-3 py-2">
              <dt className="capitalize text-dim">{k.replace(/_/g, " ")}</dt>
              <dd>
                {typeof v === "boolean" ? (
                  <StatusDot state={v ? "up" : "idle"} label={v ? "enabled" : "disabled"} />
                ) : (
                  <span className="font-mono text-2xs text-dim">{String(v)}</span>
                )}
              </dd>
            </div>
          ))}
        </dl>
        <p className="px-3 py-2 text-2xs text-faint">
          Toggle via <span className="font-mono">SIEM_ENABLE_ML</span>,{" "}
          <span className="font-mono">SIEM_AUTH_ENABLED</span>,{" "}
          <span className="font-mono">SIEM_ENABLE_LLM_ASSIST</span> and restart.
        </p>
      </Panel>

      <Panel title="Detection Thresholds (live)">
        {rulesQ.data && (
          <div className="divide-y divide-line">
            {rulesQ.data.rules
              .filter((r) => Object.keys(r.parameters).length > 0)
              .map((r) => (
                <div key={r.rule_id} className="px-3 py-2">
                  <div className="font-mono text-[12px] text-ink">{r.handle}</div>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {Object.entries(r.parameters).map(([k, v]) => (
                      <span
                        key={k}
                        className="rounded border border-line bg-elev px-2 py-0.5 font-mono text-2xs text-dim"
                      >
                        {k}={JSON.stringify(v)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        )}
        <p className="px-3 py-2 text-2xs text-faint">
          Configured via <span className="font-mono">SIEM_RULE_*</span> and{" "}
          <span className="font-mono">SIEM_ANOMALY_*</span> environment variables.
        </p>
      </Panel>

      <Panel title="About">
        <div className="space-y-1.5 p-3 text-[12px] text-dim">
          <p>
            Real-Time Distributed Enterprise SIEM Engine — a portfolio-grade platform for security
            event ingestion, streaming, detection, anomaly analysis and alert correlation.
          </p>
          <p className="text-2xs text-faint">
            Built by Veer Shah · MIT License · not a production SIEM (see project README).
          </p>
        </div>
      </Panel>
    </div>
  );
}
