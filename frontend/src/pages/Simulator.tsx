import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, Field } from "@/components/ui/primitives";
import { StatusDot } from "@/components/ui/badges";
import { Icon } from "@/components/ui/Icon";

const SCENARIO_LABEL: Record<string, string> = {
  normal: "Normal Traffic",
  ssh_brute_force: "SSH Brute Force",
  password_spray: "Password Spraying",
  credential_attack: "Credential Attack",
  port_scan: "Port Scan",
  privilege_escalation: "Privilege Escalation",
  suspicious_sql: "Suspicious SQL",
  sql_attack: "Suspicious SQL",
  data_exfiltration: "Data Exfiltration",
  web_attack: "Web Attack",
  mixed: "Mixed (normal + attacks)",
};

export function Simulator() {
  const qc = useQueryClient();
  const { lastAlert } = useRealtime();
  const statusQ = useQuery({
    queryKey: ["sim-status"],
    queryFn: api.simulatorStatus,
    refetchInterval: 3000,
  });
  const scenariosQ = useQuery({ queryKey: ["sim-scenarios"], queryFn: api.simulatorScenarios });

  const [rate, setRate] = useState(60);
  const [scenario, setScenario] = useState("mixed");
  const [attackRatio, setAttackRatio] = useState(0.06);

  useEffect(() => {
    const d = statusQ.data?.desired;
    if (d) {
      setRate(d.rate);
      setScenario(d.scenario);
      setAttackRatio(d.attack_ratio);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusQ.data?.desired?.rate, statusQ.data?.desired?.scenario]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["sim-status"] });
  const start = useMutation({
    mutationFn: () => api.simulatorStart({ rate, scenario, attack_ratio: attackRatio }),
    onSuccess: invalidate,
  });
  const stop = useMutation({ mutationFn: api.simulatorStop, onSuccess: invalidate });
  const configure = useMutation({
    mutationFn: () => api.simulatorConfigure({ rate, scenario, attack_ratio: attackRatio }),
    onSuccess: invalidate,
  });
  const burst = useMutation({
    mutationFn: () => api.simulatorConfigure({ burst: true }),
    onSuccess: invalidate,
  });

  if (statusQ.isLoading) return <Loading />;
  if (statusQ.isError) return <ErrorState error={statusQ.error} retry={() => statusQ.refetch()} />;

  const s = statusQ.data!;
  const d = s.desired;
  const stats = s.stats as Record<string, number | string>;
  const scenarios = scenariosQ.data?.scenarios ?? Object.keys(SCENARIO_LABEL);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Attack Simulator"
        subtitle="Synthetic defensive simulation — generates fabricated log events only"
      />

      <div className="rounded-lg border border-[var(--sev-medium)]/35 bg-[var(--sev-medium)]/8 px-3.5 py-2.5 text-[11.5px] text-sev-medium">
        <span className="font-semibold">Synthetic Defensive Simulation.</span> This control panel
        produces fabricated security-log events for detection engineering and demos. It never scans,
        connects to, or attacks any real host or network. All addresses are RFC&nbsp;1918 or
        documentation (TEST-NET) ranges.
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Control Panel" className="lg:col-span-2">
          <div className="space-y-5 p-4">
            <div className="flex items-center gap-2.5">
              <StatusDot state={s.simulator_connected ? "up" : "down"} pulse />
              <span className="text-[12.5px] text-dim">
                Generator {s.simulator_connected ? "connected" : "not connected"} ·{" "}
                <span className={d.running ? "text-ok" : "text-idle"}>
                  {d.running ? "running" : "stopped"}
                </span>
              </span>
            </div>

            <div>
              <label className="text-2xs font-semibold uppercase tracking-[0.06em] text-faint">
                Scenario
              </label>
              <div className="mt-2 grid grid-cols-2 gap-1.5 sm:grid-cols-3">
                {scenarios.map((sc) => (
                  <button
                    key={sc}
                    onClick={() => setScenario(sc)}
                    className={cn(
                      "rounded border px-2.5 py-2 text-left text-[11.5px] font-medium transition-colors",
                      scenario === sc
                        ? "border-accent bg-accent/12 text-ink"
                        : "border-line-strong text-dim hover:bg-panel-2",
                    )}
                  >
                    {SCENARIO_LABEL[sc] ?? sc}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-2xs font-semibold uppercase tracking-[0.06em] text-faint">
                  Intensity — {rate} events/sec
                </label>
                <input
                  type="range"
                  min={0}
                  max={2000}
                  step={10}
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                  className="mt-2 w-full accent-[var(--accent)]"
                />
                <div className="mt-1 flex gap-1">
                  {[10, 50, 100, 500, 1000].map((r) => (
                    <button key={r} className="btn btn-xs btn-ghost" onClick={() => setRate(r)}>
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-2xs font-semibold uppercase tracking-[0.06em] text-faint">
                  Attack ratio (mixed) — {(attackRatio * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={0.5}
                  step={0.01}
                  value={attackRatio}
                  onChange={(e) => setAttackRatio(Number(e.target.value))}
                  className="mt-2 w-full accent-[var(--accent)]"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button className="btn btn-primary" disabled={start.isPending} onClick={() => start.mutate()}>
                <Icon.play size={12} /> Start Simulation
              </button>
              <button className="btn" disabled={stop.isPending} onClick={() => stop.mutate()}>
                <Icon.pause size={12} /> Stop
              </button>
              <button className="btn" disabled={configure.isPending} onClick={() => configure.mutate()}>
                Apply Config
              </button>
              <button className="btn" disabled={burst.isPending} onClick={() => burst.mutate()}>
                <Icon.bolt size={12} /> Burst (10× for 8s)
              </button>
            </div>
          </div>
        </Panel>

        <div className="space-y-4">
          <Panel title="Live Generator Stats">
            <dl className="divide-y divide-line text-[12px]">
              {[
                ["Scenario", SCENARIO_LABEL[d.scenario] ?? d.scenario],
                ["Target rate", `${d.rate} eps`],
                ["Effective eps", stats.effective_eps ?? "—"],
                ["Events sent", stats.sent_total ?? "—"],
                ["Attack events", stats.sent_attack_events ?? "—"],
                ["Scenario runs", stats.scenario_runs ?? "—"],
                ["Queue depth", stats.queue_depth ?? "—"],
                ["Uptime (s)", stats.uptime_seconds ?? "—"],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between px-3 py-1.5">
                  <dt className="text-faint">{k}</dt>
                  <dd className="tnum text-dim">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </Panel>
          <Panel title="Most Recent Alert">
            <div className="p-3 text-[12px]">
              {lastAlert ? (
                <>
                  <Field label={lastAlert.rule_id}>
                    <span className="text-ink">{lastAlert.title}</span>
                  </Field>
                  <div className="mt-1 text-2xs text-faint">
                    {lastAlert.severity} · ×{lastAlert.event_count} events
                  </div>
                </>
              ) : (
                <span className="text-faint">Waiting for an alert…</span>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
