import { cn } from "@/lib/cn";
import type { Alert, SecurityEvent } from "@/types";
import { clockTime, fullTime } from "@/lib/format";
import { eventTypeLabel } from "@/lib/severity";

interface Node {
  at: string;
  label: string;
  kind: "event" | "alert" | "status";
  detail?: string;
}

export function AlertTimeline({ alert, events }: { alert: Alert; events: SecurityEvent[] }) {
  const nodes: Node[] = [];

  // contributing events (evidence + any correlated recent events, de-duped by id)
  const seen = new Set<string>();
  for (const ev of alert.evidence) {
    seen.add(ev.event_id);
    nodes.push({ at: ev.timestamp, label: ev.summary, kind: "event" });
  }
  for (const e of events) {
    if (seen.has(e.event_id)) continue;
    if (new Date(e.timestamp) > new Date(alert.last_seen)) continue;
    nodes.push({
      at: e.timestamp,
      label: `${eventTypeLabel(e.event_type)}${e.username ? ` · ${e.username}` : ""}${
        e.status ? ` · ${e.status}` : ""
      }`,
      kind: "event",
    });
  }

  nodes.push({
    at: alert.first_seen,
    label: "Correlation window opened",
    kind: "alert",
  });
  nodes.push({
    at: alert.last_seen,
    label: `${alert.title} — alert raised (×${alert.event_count})`,
    kind: "alert",
  });

  for (const h of alert.metadata?.status_history ?? []) {
    nodes.push({
      at: h.at,
      label: `Status → ${h.to.replace("_", " ")}`,
      detail: `by ${h.by}`,
      kind: "status",
    });
  }

  nodes.sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime());

  return (
    <ol className="relative ml-2 space-y-3 border-l border-line pl-4">
      {nodes.map((n, i) => (
        <li key={i} className="relative">
          <span
            className={cn(
              "absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-bg",
              n.kind === "alert"
                ? "bg-[var(--sev-high)]"
                : n.kind === "status"
                  ? "bg-accent"
                  : "bg-line-strong",
            )}
          />
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-[10.5px] text-faint" title={fullTime(n.at)}>
              {clockTime(n.at)}
            </span>
            <span
              className={cn(
                "text-[11.5px]",
                n.kind === "alert" ? "font-semibold text-sev-high" : "text-dim",
              )}
            >
              {n.label}
            </span>
            {n.detail && <span className="text-2xs text-faint">{n.detail}</span>}
          </div>
        </li>
      ))}
    </ol>
  );
}
