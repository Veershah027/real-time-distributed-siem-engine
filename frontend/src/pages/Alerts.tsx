import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card, Loading, ErrorState, SeverityBadge, StatusPill } from "@/components/primitives";
import { AlertDetail } from "@/components/AlertDetail";
import { relTime, pct } from "@/lib/format";

const STATUSES = ["open", "acknowledged", "resolved", "false_positive"];
const SEVERITIES = ["critical", "high", "medium", "low"];
const PAGE = 25;

export function Alerts() {
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["alerts", status, severity, offset],
    queryFn: () =>
      api.alerts({
        status: status || undefined,
        severity: severity || undefined,
        limit: PAGE,
        offset,
      }),
    placeholderData: keepPreviousData,
    refetchInterval: 6000,
  });

  const total = query.data?.total ?? 0;

  return (
    <Card
      title={`Alerts${total ? ` — ${total}` : ""}`}
      action={
        <div className="flex gap-2">
          <select
            className="input"
            value={status}
            onChange={(e) => {
              setOffset(0);
              setStatus(e.target.value);
            }}
          >
            <option value="">all statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
          <select
            className="input"
            value={severity}
            onChange={(e) => {
              setOffset(0);
              setSeverity(e.target.value);
            }}
          >
            <option value="">all severities</option>
            {SEVERITIES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      }
    >
      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : (
        <>
          <div className="max-h-[calc(100vh-16rem)] overflow-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead>
                <tr>
                  <th className="th">Severity</th>
                  <th className="th">Rule</th>
                  <th className="th">Title</th>
                  <th className="th">Source IP</th>
                  <th className="th">Host</th>
                  <th className="th">Events</th>
                  <th className="th">Confidence</th>
                  <th className="th">Status</th>
                  <th className="th">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {(query.data?.items ?? []).map((a) => (
                  <tr
                    key={a.alert_id}
                    className="row-hover cursor-pointer border-b border-base-750"
                    onClick={() => setSelected(a.alert_id)}
                  >
                    <td className="td">
                      <SeverityBadge severity={a.severity} />
                    </td>
                    <td className="td font-mono text-xs text-slate-400">{a.rule_id}</td>
                    <td className="td max-w-xs truncate text-slate-200">{a.title}</td>
                    <td className="td font-mono text-xs text-slate-300">{a.source_ip ?? "—"}</td>
                    <td className="td text-slate-400">{a.affected_host ?? "—"}</td>
                    <td className="td tabular-nums text-slate-300">{a.event_count}</td>
                    <td className="td tabular-nums text-slate-400">{pct(a.confidence)}</td>
                    <td className="td">
                      <StatusPill status={a.status} />
                    </td>
                    <td className="td text-xs text-slate-500">{relTime(a.last_seen)}</td>
                  </tr>
                ))}
                {(query.data?.items.length ?? 0) === 0 && (
                  <tr>
                    <td colSpan={9} className="td py-12 text-center text-slate-500">
                      No alerts match the current filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-base-700 px-4 py-2 text-xs text-slate-400">
            <span>
              {total === 0 ? 0 : offset + 1}–{Math.min(offset + PAGE, total)} of {total}
            </span>
            <div className="flex gap-2">
              <button
                className="btn-ghost"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
              >
                Prev
              </button>
              <button
                className="btn-ghost"
                disabled={offset + PAGE >= total}
                onClick={() => setOffset(offset + PAGE)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}

      {selected && <AlertDetail alertId={selected} onClose={() => setSelected(null)} />}
    </Card>
  );
}
