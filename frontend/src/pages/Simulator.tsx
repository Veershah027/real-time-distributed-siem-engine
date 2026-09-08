import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "@/services/api";
import { Card, Loading, ErrorState } from "@/components/primitives";
import { useRealtimeContext } from "@/hooks/realtimeContext";

const SCENARIO_LABELS: Record<string, string> = {
  normal: "Normal traffic",
  ssh_brute_force: "SSH brute force",
  port_scan: "Port scan",
  credential_attack: "Credential attack / spray",
  privilege_escalation: "Privilege escalation",
  data_exfiltration: "Data exfiltration",
  web_attack: "Web attack",
  mixed: "Mixed (normal + attacks)",
};

export function Simulator() {
  const qc = useQueryClient();
  const { lastAlert } = useRealtimeContext();
  const status = useQuery({
    queryKey: ["sim-status"],
    queryFn: api.simulatorStatus,
    refetchInterval: 3000,
  });
  const scenarios = useQuery({
    queryKey: ["sim-scenarios"],
    queryFn: api.simulatorScenarios,
  });

  const [rate, setRate] = useState(60);
  const [scenario, setScenario] = useState("mixed");
  const [attackRatio, setAttackRatio] = useState(0.06);

  useEffect(() => {
    if (status.data?.desired) {
      setRate(status.data.desired.rate);
      setScenario(status.data.desired.scenario);
      setAttackRatio(status.data.desired.attack_ratio);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status.data?.desired?.rate, status.data?.desired?.scenario]);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["sim-status"] });
  };

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

  if (status.isLoading) return <Loading />;
  if (status.isError) return <ErrorState error={status.error} />;

  const d = status.data!.desired;
  const connected = status.data!.simulator_connected;
  const stats = (status.data!.stats ?? {}) as Record<string, number>;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card title="Control panel" className="lg:col-span-2">
        <div className="space-y-5 p-5">
          <div className="flex items-center gap-3">
            <span
              className={clsx(
                "h-2.5 w-2.5 rounded-full",
                connected ? "bg-emerald-400" : "bg-sev-critical animate-pulse",
              )}
            />
            <span className="text-sm text-slate-300">
              Simulator {connected ? "connected" : "not connected"} ·{" "}
              {d.running ? "running" : "stopped"}
            </span>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Scenario
            </label>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {(scenarios.data?.scenarios ?? Object.keys(SCENARIO_LABELS)).map((s) => (
                <button
                  key={s}
                  onClick={() => setScenario(s)}
                  className={clsx(
                    "rounded-md border px-2.5 py-2 text-xs font-medium transition-colors",
                    scenario === s
                      ? "border-accent bg-accent-600/20 text-white"
                      : "border-base-600 text-slate-400 hover:bg-base-700",
                  )}
                >
                  {SCENARIO_LABELS[s] ?? s}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Rate — {rate} events/sec
              </label>
              <input
                type="range"
                min={0}
                max={2000}
                step={10}
                value={rate}
                onChange={(e) => setRate(Number(e.target.value))}
                className="mt-2 w-full accent-accent"
              />
              <div className="mt-1 flex gap-1">
                {[10, 50, 100, 500, 1000].map((r) => (
                  <button key={r} className="btn-ghost px-2 py-0.5 text-xs" onClick={() => setRate(r)}>
                    {r}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Attack ratio (mixed) — {(attackRatio * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min={0}
                max={0.5}
                step={0.01}
                value={attackRatio}
                onChange={(e) => setAttackRatio(Number(e.target.value))}
                className="mt-2 w-full accent-accent"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button className="btn-primary" onClick={() => start.mutate()} disabled={start.isPending}>
              ▶ Start
            </button>
            <button className="btn-ghost" onClick={() => stop.mutate()} disabled={stop.isPending}>
              ■ Stop
            </button>
            <button
              className="btn-ghost"
              onClick={() => configure.mutate()}
              disabled={configure.isPending}
            >
              Apply config
            </button>
            <button className="btn-ghost" onClick={() => burst.mutate()} disabled={burst.isPending}>
              ⚡ Burst (10× for 8s)
            </button>
          </div>
          <p className="text-xs text-slate-500">
            The simulator only produces synthetic events to the broker. It never touches a real
            host or network. Changes propagate through Redis to the simulator container within a
            few seconds.
          </p>
        </div>
      </Card>

      <div className="space-y-4">
        <Card title="Live simulator stats">
          <dl className="divide-y divide-base-750 text-sm">
            {[
              ["Desired scenario", SCENARIO_LABELS[d.scenario] ?? d.scenario],
              ["Desired rate", `${d.rate} eps`],
              ["Effective eps", stats.effective_eps ?? "—"],
              ["Events sent", stats.sent_total ?? "—"],
              ["Attack events", stats.sent_attack_events ?? "—"],
              ["Scenario runs", stats.scenario_runs ?? "—"],
              ["Queue depth", stats.queue_depth ?? "—"],
              ["Uptime (s)", stats.uptime_seconds ?? "—"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between px-4 py-2">
                <dt className="text-slate-500">{k}</dt>
                <dd className="tabular-nums text-slate-300">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </Card>
        <Card title="Most recent alert">
          <div className="p-4 text-sm">
            {lastAlert ? (
              <>
                <div className="font-medium text-slate-200">{lastAlert.title}</div>
                <div className="mt-1 text-xs text-slate-500">
                  {lastAlert.rule_id} · {lastAlert.severity} · ×{lastAlert.event_count}
                </div>
              </>
            ) : (
              <span className="text-slate-500">Waiting for an alert…</span>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
