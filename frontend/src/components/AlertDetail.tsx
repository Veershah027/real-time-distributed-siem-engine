import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Alert, AlertStatus } from "@/types";
import { api } from "@/services/api";
import { fullTime, relTime, pct } from "@/lib/format";
import { SeverityBadge, StatusPill, Loading } from "./primitives";

const NEXT_STATES: Record<AlertStatus, AlertStatus[]> = {
  open: ["acknowledged", "resolved", "false_positive"],
  acknowledged: ["resolved", "false_positive", "open"],
  resolved: ["open"],
  false_positive: ["open"],
};

export function AlertDetail({ alertId, onClose }: { alertId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const { data: alert, isLoading } = useQuery({
    queryKey: ["alert", alertId],
    queryFn: () => api.alert(alertId),
    refetchInterval: 8000,
  });
  const related = useQuery({
    queryKey: ["alert-events", alertId],
    queryFn: () => api.alertEvents(alertId),
    enabled: !!alert?.source_ip,
  });

  const mutate = useMutation({
    mutationFn: (status: AlertStatus) => api.updateAlert(alertId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alert", alertId] });
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-xl overflow-y-auto border-l border-base-700 bg-base-850 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-base-700 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-100">Alert detail</h2>
          <button className="btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>

        {isLoading || !alert ? (
          <Loading />
        ) : (
          <div className="space-y-5 p-5">
            <div>
              <div className="flex items-center gap-2">
                <SeverityBadge severity={alert.severity} />
                <StatusPill status={alert.status} />
                <span className="text-xs text-slate-500">{alert.rule_id}</span>
                <span className="ml-auto rounded bg-base-700 px-1.5 py-0.5 text-[10px] uppercase text-slate-400">
                  {alert.detection_kind}
                </span>
              </div>
              <h3 className="mt-2 text-lg font-bold text-slate-100">{alert.title}</h3>
              <p className="mt-1 text-sm text-slate-400">{alert.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <Field label="Alert ID" value={alert.alert_id} mono />
              <Field label="Confidence" value={pct(alert.confidence)} />
              <Field label="Source IP" value={alert.source_ip ?? "—"} mono />
              <Field label="Affected host" value={alert.affected_host ?? "—"} />
              <Field label="Event count" value={String(alert.event_count)} />
              <Field
                label="Anomaly score"
                value={alert.anomaly_score != null ? alert.anomaly_score.toFixed(2) : "—"}
              />
              <Field label="First seen" value={`${fullTime(alert.first_seen)} (${relTime(alert.first_seen)})`} />
              <Field label="Last seen" value={`${fullTime(alert.last_seen)} (${relTime(alert.last_seen)})`} />
            </div>

            {alert.involved_users.length > 0 && (
              <Field label="Involved users" value={alert.involved_users.join(", ")} />
            )}
            {alert.involved_hosts.length > 0 && (
              <Field label="Involved hosts" value={alert.involved_hosts.join(", ")} />
            )}

            <div>
              <SectionLabel>Recommended response</SectionLabel>
              <p className="mt-1 rounded-md border border-base-700 bg-base-800 p-3 text-sm text-slate-300">
                {alert.recommended_action}
              </p>
            </div>

            <div>
              <SectionLabel>Evidence ({alert.evidence.length})</SectionLabel>
              <ul className="mt-1 space-y-1">
                {alert.evidence.map((ev, i) => (
                  <li
                    key={i}
                    className="rounded border border-base-700 bg-base-800 px-3 py-1.5 text-xs text-slate-400"
                  >
                    <span className="font-mono text-slate-500">{fullTime(ev.timestamp)}</span> —{" "}
                    {ev.summary}
                  </li>
                ))}
              </ul>
            </div>

            {alert.source_ip && (
              <div>
                <SectionLabel>
                  Related events from {alert.source_ip} ({related.data?.count ?? 0})
                </SectionLabel>
                <ul className="mt-1 max-h-52 space-y-1 overflow-y-auto">
                  {(related.data?.events ?? []).map((e) => (
                    <li key={e.event_id} className="text-xs text-slate-500">
                      <span className="font-mono">{fullTime(e.timestamp)}</span> · {e.event_type} ·{" "}
                      {e.username ?? "—"} · {e.status ?? "—"}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <SectionLabel>Triage</SectionLabel>
              <div className="mt-2 flex flex-wrap gap-2">
                {NEXT_STATES[alert.status].map((s) => (
                  <button
                    key={s}
                    className="btn-primary"
                    disabled={mutate.isPending}
                    onClick={() => mutate.mutate(s)}
                  >
                    Mark {s.replace("_", " ")}
                  </button>
                ))}
              </div>
              {mutate.isError && (
                <p className="mt-2 text-xs text-sev-critical">
                  {(mutate.error as Error).message}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
      {children}
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div className={mono ? "break-all font-mono text-xs text-slate-300" : "text-slate-300"}>
        {value}
      </div>
    </div>
  );
}
