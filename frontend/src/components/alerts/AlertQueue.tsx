import { cn } from "@/lib/cn";
import type { Alert } from "@/types";
import { relTime } from "@/lib/format";
import { severityColor } from "@/lib/severity";
import { Confidence, SeverityBadge, StatusBadge } from "@/components/ui/badges";
import { EmptyState } from "@/components/ui/primitives";
import { Icon } from "@/components/ui/Icon";

export function AlertQueue({
  alerts,
  onSelect,
  activeId,
  flashFirst,
  emptyHint,
}: {
  alerts: Alert[];
  onSelect: (id: string) => void;
  activeId?: string;
  flashFirst?: boolean;
  emptyHint?: string;
}) {
  if (alerts.length === 0) {
    return (
      <EmptyState
        title="No alerts"
        hint={emptyHint ?? "Run an attack scenario from the Simulator to generate one."}
        icon={<Icon.shield size={22} />}
      />
    );
  }
  return (
    <ul className="divide-y divide-line">
      {alerts.map((a, i) => (
        <li
          key={a.alert_id}
          onClick={() => onSelect(a.alert_id)}
          className={cn(
            "relative cursor-pointer px-3 py-2.5 pl-4 transition-colors hover:bg-panel-2",
            activeId === a.alert_id && "bg-panel-2",
            flashFirst && i === 0 && "flash-row",
          )}
        >
          <span
            className="absolute inset-y-0 left-0 w-[3px]"
            style={{ background: severityColor(a.severity) }}
          />
          <div className="flex items-center gap-2">
            <SeverityBadge severity={a.severity} />
            <span className="truncate text-[12.5px] font-medium text-ink">{a.title}</span>
            <span className="ml-auto shrink-0 text-2xs text-faint">{relTime(a.last_seen)}</span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-2xs text-faint">
            <span className="font-mono">{a.rule_id}</span>
            {a.source_ip && <span className="font-mono">{a.source_ip}</span>}
            {a.affected_host && <span>{a.affected_host}</span>}
            <span className="tnum">×{a.event_count} events</span>
            <Confidence value={a.confidence} />
            <span className="ml-auto">
              <StatusBadge status={a.status} />
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
