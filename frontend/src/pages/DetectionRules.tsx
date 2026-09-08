import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { relTime } from "@/lib/format";
import { ruleCondition } from "@/lib/ruleLogic";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, StatCard, Field } from "@/components/ui/primitives";
import { SeverityBadge, StatusDot } from "@/components/ui/badges";
import { Icon } from "@/components/ui/Icon";
import type { DetectionRule } from "@/types";

export function DetectionRules() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["detections"],
    queryFn: api.detections,
    refetchInterval: 15000,
  });
  const [expanded, setExpanded] = useState<string | null>(null);

  if (isLoading) return <Loading />;
  if (isError) return <ErrorState error={error} retry={() => refetch()} />;

  const rules = data!.rules;
  const byCat = rules.reduce<Record<string, DetectionRule[]>>((acc, r) => {
    (acc[r.category] ??= []).push(r);
    return acc;
  }, {});
  const enabled = rules.filter((r) => r.enabled).length;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Detection Rules"
        subtitle="Deterministic rules are the source of truth; anomaly / ML entries are advisory"
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Rules Loaded" value={rules.length} />
        <StatCard label="Enabled" value={enabled} tone="ok" />
        <StatCard label="Total Triggers" value={data!.total_triggers.toLocaleString()} />
        <StatCard
          label="Rules Fired"
          value={rules.filter((r) => r.trigger_count > 0).length}
          tone="high"
        />
      </div>

      {Object.entries(byCat).map(([cat, items]) => (
        <Panel key={cat} title={cat}>
          <div className="divide-y divide-line">
            {items.map((r) => {
              const open = expanded === r.rule_id;
              return (
                <div key={r.rule_id}>
                  <button
                    className="flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-panel-2"
                    onClick={() => setExpanded(open ? null : r.rule_id)}
                  >
                    <Icon.chevron
                      size={13}
                      className={`shrink-0 text-faint transition-transform ${open ? "rotate-90" : ""}`}
                    />
                    <span className="font-mono text-[12px] font-semibold text-ink">{r.handle}</span>
                    <span className="text-2xs text-faint">{r.rule_id}</span>
                    <SeverityBadge severity={r.default_severity} />
                    <span className="hidden truncate text-[11.5px] text-dim sm:block">{r.name}</span>
                    <div className="ml-auto flex shrink-0 items-center gap-4 text-2xs text-faint">
                      <span className="tnum">
                        {r.trigger_count.toLocaleString()} triggers
                      </span>
                      <span>{r.last_triggered ? relTime(r.last_triggered) : "never"}</span>
                      <StatusDot state={r.enabled ? "up" : "idle"} label={r.enabled ? "Enabled" : "Off"} />
                    </div>
                  </button>
                  {open && (
                    <div className="grid gap-3 border-t border-line bg-elev/40 px-9 py-3 sm:grid-cols-2">
                      <Field label="Description">
                        <span className="text-[12px] text-dim">{r.description}</span>
                      </Field>
                      <Field label="Trigger Condition">
                        <span className="text-[12px] leading-relaxed text-dim">
                          {ruleCondition(r, r.rule_id)}
                        </span>
                      </Field>
                      {Object.keys(r.parameters).length > 0 && (
                        <Field label="Live Parameters">
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
                        </Field>
                      )}
                      {r.mitre_attack.length > 0 && (
                        <Field label="MITRE ATT&CK">{r.mitre_attack.join(", ")}</Field>
                      )}
                      <div className="sm:col-span-2">
                        <Field label="Recommended Response">
                          <span className="text-[12px] text-dim">{r.recommended_action}</span>
                        </Field>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>
      ))}
      <p className="text-2xs text-faint">
        Thresholds are configurable via <span className="font-mono">SIEM_RULE_*</span> environment
        variables — see <span className="font-mono">docs/detection-rules.md</span>.
      </p>
    </div>
  );
}
