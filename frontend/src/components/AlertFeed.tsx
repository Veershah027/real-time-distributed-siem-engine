import clsx from "clsx";
import type { Alert } from "@/types";
import { relTime, pct } from "@/lib/format";
import { SeverityBadge, StatusPill, EmptyState } from "./primitives";

export function AlertFeed({
  alerts,
  onSelect,
  highlightNew = false,
}: {
  alerts: Alert[];
  onSelect: (id: string) => void;
  highlightNew?: boolean;
}) {
  if (alerts.length === 0) {
    return (
      <EmptyState
        title="No alerts"
        hint="Run an attack scenario from the Simulator page to generate one."
      />
    );
  }
  return (
    <ul className="divide-y divide-base-750">
      {alerts.map((a, i) => (
        <li
          key={a.alert_id}
          className={clsx(
            "cursor-pointer px-4 py-3 transition-colors hover:bg-base-750",
            highlightNew && i === 0 && "animate-pulse-row",
          )}
          onClick={() => onSelect(a.alert_id)}
        >
          <div className="flex items-center gap-2">
            <SeverityBadge severity={a.severity} />
            <span className="truncate text-sm font-medium text-slate-200">{a.title}</span>
            <span className="ml-auto shrink-0 text-[11px] text-slate-500">
              {relTime(a.last_seen)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500">
            <span className="font-mono">{a.rule_id}</span>
            {a.source_ip && <span className="font-mono">{a.source_ip}</span>}
            {a.affected_host && <span>{a.affected_host}</span>}
            <span>×{a.event_count}</span>
            <span>conf {pct(a.confidence)}</span>
            <StatusPill status={a.status} />
          </div>
        </li>
      ))}
    </ul>
  );
}
