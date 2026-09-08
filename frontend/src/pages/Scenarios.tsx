import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel } from "@/components/ui/primitives";
import { Icon } from "@/components/ui/Icon";
import { SeverityBadge } from "@/components/ui/badges";
import type { Severity } from "@/types";

interface Scenario {
  id: string;
  name: string;
  desc: string;
  triggers: string;
  severity: Severity;
}

const SCENARIOS: Scenario[] = [
  {
    id: "ssh_brute_force",
    name: "SSH Brute Force",
    desc: "Repeated failed SSH authentication from one source IP against several accounts, then a successful login.",
    triggers: "RULE-001",
    severity: "high",
  },
  {
    id: "credential_attack",
    name: "Password Spraying",
    desc: "One source IP attempts one password against many distinct accounts — low and slow.",
    triggers: "RULE-002",
    severity: "high",
  },
  {
    id: "port_scan",
    name: "Port Scan",
    desc: "One source IP contacts dozens of destination ports on a host in a short window.",
    triggers: "RULE-003",
    severity: "high",
  },
  {
    id: "privilege_escalation",
    name: "Privilege Escalation",
    desc: "A normal user runs sudo / admin commands, often outside business hours.",
    triggers: "RULE-004",
    severity: "high",
  },
  {
    id: "sql_attack",
    name: "Suspicious SQL",
    desc: "Synthetic database logs containing UNION SELECT, tautologies and file-access patterns. No SQL is executed.",
    triggers: "RULE-005",
    severity: "medium",
  },
  {
    id: "data_exfiltration",
    name: "Data Exfiltration",
    desc: "Sustained large outbound transfer from an internal host to one external destination.",
    triggers: "RULE-006",
    severity: "medium",
  },
  {
    id: "web_attack",
    name: "Web Attack",
    desc: "Scanner user-agent hitting sensitive paths with repeated 4xx / 5xx responses.",
    triggers: "RULE-001 / RULE-007",
    severity: "medium",
  },
];

export function Scenarios() {
  const navigate = useNavigate();
  const [fired, setFired] = useState<string | null>(null);

  const run = useMutation({
    mutationFn: (id: string) =>
      api.simulatorConfigure({ scenario: id, rate: 120 }).then(() =>
        api.simulatorStart({ scenario: id, rate: 120 }),
      ),
    onSuccess: (_d, id) => {
      setFired(id);
      setTimeout(() => setFired(null), 4000);
    },
  });

  return (
    <div className="space-y-4">
      <PageHeader
        title="Demo Scenarios"
        subtitle="One click sets the generator to a dedicated attack scenario — synthetic, local only"
      />

      <div className="rounded-lg border border-[var(--sev-medium)]/35 bg-[var(--sev-medium)]/8 px-3.5 py-2.5 text-[11.5px] text-sev-medium">
        <span className="font-semibold">Synthetic Defensive Simulation.</span> Running a scenario
        switches the log generator; it does not launch any real attack.
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {SCENARIOS.map((s) => (
          <Panel key={s.id} className="flex flex-col">
            <div className="flex flex-1 flex-col gap-2 p-3.5">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-ink">{s.name}</span>
                <SeverityBadge severity={s.severity} />
              </div>
              <p className="text-[11.5px] leading-relaxed text-dim">{s.desc}</p>
              <div className="mt-auto flex items-center justify-between pt-2">
                <span className="font-mono text-2xs text-faint">triggers {s.triggers}</span>
                <button
                  className="btn btn-xs btn-primary"
                  disabled={run.isPending}
                  onClick={() => run.mutate(s.id)}
                >
                  {fired === s.id ? (
                    <>
                      <Icon.check size={11} /> Running
                    </>
                  ) : (
                    <>
                      <Icon.play size={11} /> Run scenario
                    </>
                  )}
                </button>
              </div>
            </div>
          </Panel>
        ))}
      </div>

      <div className="flex items-center gap-2 text-[11.5px] text-faint">
        Then watch{" "}
        <button className="text-accent hover:underline" onClick={() => navigate("/events")}>
          Live Events
        </button>{" "}
        and{" "}
        <button className="text-accent hover:underline" onClick={() => navigate("/alerts")}>
          Alerts
        </button>{" "}
        — an alert typically appears within ~10 seconds.
      </div>
    </div>
  );
}
