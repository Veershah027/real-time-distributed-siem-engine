import { useState } from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/cn";
import type { SecurityEvent } from "@/types";
import { clockTime } from "@/lib/format";
import { eventTypeLabel, severityColor } from "@/lib/severity";
import { Icon } from "@/components/ui/Icon";
import { EmptyState } from "@/components/ui/primitives";
import { EventDetail } from "./EventDetail";

const FAIL = new Set(["failure", "denied", "error", "blocked"]);

export function EventStream({
  events,
  paused,
  onPause,
  onClear,
  compact,
  liveCount,
}: {
  events: SecurityEvent[];
  paused: boolean;
  onPause: (v: boolean) => void;
  onClear?: () => void;
  compact?: boolean;
  liveCount?: number;
}) {
  const [selected, setSelected] = useState<SecurityEvent | null>(null);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b border-line px-2.5 py-1.5">
        <div className="flex items-center gap-2 text-2xs text-faint">
          <span
            className={cn("h-1.5 w-1.5 rounded-full", paused ? "bg-idle" : "bg-ok pulse-dot")}
          />
          {paused ? "Stream paused" : "Live"}
          {liveCount !== undefined && (
            <span className="tnum">· {liveCount.toLocaleString()} received</span>
          )}
          <span className="tnum">· {events.length} shown</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            className="btn btn-xs btn-ghost"
            onClick={() => onPause(!paused)}
            aria-pressed={paused}
          >
            {paused ? <Icon.play size={11} /> : <Icon.pause size={11} />}
            {paused ? "Resume" : "Pause"}
          </button>
          {onClear && (
            <button className="btn btn-xs btn-ghost" onClick={onClear}>
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        {events.length === 0 ? (
          <EmptyState
            title="Waiting for events"
            hint="The stream processor publishes each ingested event here in real time."
            icon={<Icon.activity size={22} />}
          />
        ) : (
          <table className="w-full border-separate border-spacing-0">
            <thead>
              <tr>
                <th className="th w-16">Time</th>
                <th className="th w-24">Source</th>
                <th className="th">Type</th>
                <th className="th w-32">Source IP</th>
                {!compact && <th className="th w-40">Destination</th>}
                <th className="th w-20">User</th>
                <th className="th w-16">Status</th>
                {!compact && <th className="th">Message</th>}
              </tr>
            </thead>
            <tbody>
              {events.map((e, i) => (
                <tr
                  key={e.event_id}
                  onClick={() => setSelected(e)}
                  className={cn("row-hover cursor-pointer", i === 0 && !paused && "flash-row")}
                >
                  <td className="td relative !py-1.5 font-mono text-[11px] text-faint">
                    <span
                      className="absolute inset-y-0 left-0 w-[3px]"
                      style={{ background: severityColor(e.severity) }}
                    />
                    {clockTime(e.timestamp)}
                  </td>
                  <td className="td !py-1.5 text-[11.5px] text-dim">{e.source}</td>
                  <td className="td !py-1.5 text-[12px] text-ink">{eventTypeLabel(e.event_type)}</td>
                  <td className="td !py-1.5">
                    {e.source_ip ? (
                      <Link
                        to={`/events?source_ip=${e.source_ip}`}
                        onClick={(ev) => ev.stopPropagation()}
                        className="mono-cell hover:text-accent"
                      >
                        {e.source_ip}
                      </Link>
                    ) : (
                      <span className="text-faint">—</span>
                    )}
                  </td>
                  {!compact && (
                    <td className="td !py-1.5 mono-cell">
                      {e.destination_ip
                        ? `${e.destination_ip}${e.destination_port ? `:${e.destination_port}` : ""}`
                        : "—"}
                    </td>
                  )}
                  <td className="td !py-1.5 text-[11.5px] text-dim">{e.username ?? "—"}</td>
                  <td className="td !py-1.5">
                    <span
                      className={cn(
                        "text-[11px]",
                        FAIL.has(e.status ?? "") ? "text-sev-high" : "text-faint",
                      )}
                    >
                      {e.status ?? "—"}
                    </span>
                  </td>
                  {!compact && (
                    <td className="td !py-1.5 max-w-sm truncate font-mono text-[10.5px] text-faint">
                      {e.message ?? "—"}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <EventDetail event={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
