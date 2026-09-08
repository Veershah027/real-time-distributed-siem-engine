import clsx from "clsx";
import type { SecurityEvent } from "@/types";
import { clockTime } from "@/lib/format";
import { SeverityBadge, EmptyState } from "./primitives";

export function EventTable({
  events,
  highlightNew = false,
  dense = false,
}: {
  events: SecurityEvent[];
  highlightNew?: boolean;
  dense?: boolean;
}) {
  if (events.length === 0) {
    return <EmptyState title="No events yet" hint="Start the simulator to see live traffic." />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0">
        <thead>
          <tr>
            <th className="th">Time</th>
            <th className="th">Severity</th>
            <th className="th">Type</th>
            <th className="th">Source</th>
            <th className="th">Source IP</th>
            <th className="th">User</th>
            <th className="th">Status</th>
            {!dense && <th className="th">Message</th>}
          </tr>
        </thead>
        <tbody>
          {events.map((e, i) => (
            <tr
              key={e.event_id}
              className={clsx(
                "row-hover border-b border-base-750",
                highlightNew && i === 0 && "animate-pulse-row",
              )}
            >
              <td className="td font-mono text-xs text-slate-400">{clockTime(e.timestamp)}</td>
              <td className="td">
                <SeverityBadge severity={e.severity} />
              </td>
              <td className="td text-slate-300">{e.event_type}</td>
              <td className="td text-slate-400">{e.source}</td>
              <td className="td font-mono text-xs text-slate-300">{e.source_ip ?? "—"}</td>
              <td className="td text-slate-400">{e.username ?? "—"}</td>
              <td className="td">
                <span
                  className={clsx(
                    "text-xs",
                    ["failure", "denied", "error", "blocked"].includes(e.status ?? "")
                      ? "text-sev-high"
                      : "text-slate-400",
                  )}
                >
                  {e.status ?? "—"}
                </span>
              </td>
              {!dense && (
                <td className="td max-w-md truncate text-xs text-slate-500" title={e.message ?? ""}>
                  {e.message ?? "—"}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
