import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AlertStatus } from "@/types";
import { api } from "@/lib/api";
import { fullTime, relTime } from "@/lib/format";
import { ruleCondition } from "@/lib/ruleLogic";
import { Drawer } from "@/components/ui/Drawer";
import { Tabs } from "@/components/ui/Tabs";
import { CopyButton, Field, Loading } from "@/components/ui/primitives";
import { Confidence, SeverityBadge, StatusBadge } from "@/components/ui/badges";
import { IncidentWorkflow } from "./IncidentWorkflow";
import { AlertTimeline } from "./AlertTimeline";

type Tab = "overview" | "evidence" | "logic" | "timeline" | "related" | "response";

export function AlertInvestigation({ alertId, onClose }: { alertId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");

  const alertQ = useQuery({
    queryKey: ["alert", alertId],
    queryFn: () => api.alert(alertId),
    refetchInterval: 8000,
  });
  const relatedQ = useQuery({
    queryKey: ["alert-events", alertId],
    queryFn: () => api.alertEvents(alertId),
    enabled: !!alertQ.data?.source_ip,
  });
  const rulesQ = useQuery({ queryKey: ["detections"], queryFn: api.detections });

  const mutate = useMutation({
    mutationFn: (status: AlertStatus) => api.updateAlert(alertId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alert", alertId] });
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });

  const a = alertQ.data;
  const rule = rulesQ.data?.rules.find((r) => r.rule_id === a?.rule_id);
  const events = relatedQ.data?.events ?? [];

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "overview", label: "Overview" },
    { id: "evidence", label: "Evidence", count: a?.evidence.length },
    { id: "logic", label: "Detection Logic" },
    { id: "timeline", label: "Timeline" },
    { id: "related", label: "Related Events", count: relatedQ.data?.count },
    { id: "response", label: "Response" },
  ];

  return (
    <Drawer open onClose={onClose} title="Alert Investigation" width="max-w-2xl">
      {!a ? (
        <Loading />
      ) : (
        <div className="flex h-full flex-col">
          <div className="space-y-3 border-b border-line p-4">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={a.severity} dot />
              <StatusBadge status={a.status} />
              <span className="font-mono text-[11px] text-faint">{a.rule_id}</span>
              <span className="ml-auto rounded bg-panel-3 px-1.5 py-0.5 text-2xs uppercase text-faint">
                {a.detection_kind}
              </span>
            </div>
            <h2 className="text-[15px] font-semibold text-ink">{a.title}</h2>
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-2xs text-faint">
              <span>
                Source{" "}
                {a.source_ip ? (
                  <Link className="font-mono text-accent hover:underline" to={`/events?source_ip=${a.source_ip}`}>
                    {a.source_ip}
                  </Link>
                ) : (
                  "—"
                )}
              </span>
              <span>
                Target <span className="font-mono text-dim">{a.affected_host ?? "—"}</span>
              </span>
              <span>
                Events <span className="tnum text-dim">{a.event_count}</span>
              </span>
              <span>First seen {relTime(a.first_seen)}</span>
              <span>Last seen {relTime(a.last_seen)}</span>
            </div>
            <IncidentWorkflow
              status={a.status}
              pending={mutate.isPending}
              onChange={(s) => mutate.mutate(s)}
            />
            {mutate.isError && (
              <p className="text-2xs text-sev-critical">{(mutate.error as Error).message}</p>
            )}
          </div>

          <Tabs tabs={tabs} active={tab} onChange={setTab} />

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            {tab === "overview" && (
              <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                <Field label="Alert ID" mono>
                  <span className="inline-flex items-center gap-1">
                    {a.alert_id.slice(0, 18)}… <CopyButton text={a.alert_id} />
                  </span>
                </Field>
                <Field label="Confidence">
                  <Confidence value={a.confidence} />
                </Field>
                <Field label="Rule">
                  {rule?.name ?? a.rule_id}{" "}
                  <span className="font-mono text-2xs text-faint">({rule?.handle})</span>
                </Field>
                <Field label="Detection Kind">{a.detection_kind}</Field>
                <Field label="First Seen">{fullTime(a.first_seen)}</Field>
                <Field label="Last Seen">{fullTime(a.last_seen)}</Field>
                {a.anomaly_score != null && (
                  <Field label="Anomaly Score">{a.anomaly_score.toFixed(2)}</Field>
                )}
                {a.involved_users.length > 0 && (
                  <Field label="Involved Users">{a.involved_users.join(", ")}</Field>
                )}
                {a.involved_hosts.length > 0 && (
                  <Field label="Involved Hosts">{a.involved_hosts.join(", ")}</Field>
                )}
                <div className="col-span-2">
                  <Field label="Description">
                    <span className="text-[12px] text-dim">{a.description}</span>
                  </Field>
                </div>
              </div>
            )}

            {tab === "evidence" && (
              <ul className="space-y-1.5">
                {a.evidence.map((ev, i) => (
                  <li
                    key={i}
                    className="rounded border border-line bg-elev px-3 py-2 text-[11.5px] text-dim"
                  >
                    <span className="font-mono text-2xs text-faint">{fullTime(ev.timestamp)}</span>
                    <div className="mt-0.5 font-mono text-[11px]">{ev.summary}</div>
                  </li>
                ))}
                {a.evidence.length === 0 && (
                  <p className="text-xs text-faint">No evidence attached to this alert.</p>
                )}
              </ul>
            )}

            {tab === "logic" && (
              <div className="space-y-3">
                <Field label="Rule">
                  <span className="font-mono">{rule?.handle ?? a.rule_id}</span>
                </Field>
                <Field label="Condition">
                  <span className="text-[12px] leading-relaxed text-dim">
                    {ruleCondition(rule, a.rule_id)}
                  </span>
                </Field>
                {rule && Object.keys(rule.parameters).length > 0 && (
                  <Field label="Live Parameters">
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {Object.entries(rule.parameters).map(([k, v]) => (
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
                {rule && rule.mitre_attack.length > 0 && (
                  <Field label="MITRE ATT&CK">{rule.mitre_attack.join(", ")}</Field>
                )}
                <Field label="Correlation Key" mono>
                  {a.correlation_key}
                </Field>
              </div>
            )}

            {tab === "timeline" &&
              (a.evidence.length + events.length === 0 ? (
                <p className="text-xs text-faint">Not enough correlated events for a timeline.</p>
              ) : (
                <AlertTimeline alert={a} events={events} />
              ))}

            {tab === "related" && (
              <div>
                {relatedQ.isLoading ? (
                  <Loading />
                ) : events.length === 0 ? (
                  <p className="text-xs text-faint">
                    {a.source_ip
                      ? "No other recent events from this source."
                      : "This alert has no source IP to correlate on."}
                  </p>
                ) : (
                  <ul className="space-y-1">
                    {events.map((e) => (
                      <li key={e.event_id} className="font-mono text-[11px] text-faint">
                        <span className="text-dim">{fullTime(e.timestamp)}</span> · {e.event_type}
                        {e.username ? ` · ${e.username}` : ""} · {e.status ?? "—"}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {tab === "response" && (
              <div className="space-y-3">
                <div className="rounded border border-line bg-elev p-3 text-[12px] leading-relaxed text-dim">
                  {a.recommended_action}
                </div>
                <p className="text-2xs text-faint">
                  Guidance is defensive and advisory. This platform never takes automated action on
                  a target.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </Drawer>
  );
}
