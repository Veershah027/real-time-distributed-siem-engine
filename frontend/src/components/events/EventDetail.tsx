import { Link } from "react-router-dom";
import type { SecurityEvent } from "@/types";
import { fullTime } from "@/lib/format";
import { eventTypeLabel } from "@/lib/severity";
import { Drawer } from "@/components/ui/Drawer";
import { CopyButton, Field } from "@/components/ui/primitives";
import { SeverityBadge } from "@/components/ui/badges";

export function EventDetail({ event, onClose }: { event: SecurityEvent | null; onClose: () => void }) {
  return (
    <Drawer open={!!event} onClose={onClose} title="Event Detail" width="max-w-xl">
      {event && (
        <div className="space-y-4 p-4">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={event.severity} dot />
            <span className="text-[13px] font-semibold text-ink">{eventTypeLabel(event.event_type)}</span>
            <span className="ml-auto font-mono text-[11px] text-faint">{fullTime(event.timestamp)}</span>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Field label="Event ID" mono>
              <span className="inline-flex items-center gap-1">
                {event.event_id.slice(0, 18)}… <CopyButton text={event.event_id} />
              </span>
            </Field>
            <Field label="Ingested">{fullTime(event.ingested_at)}</Field>
            <Field label="Source Host">{event.source}</Field>
            <Field label="Source Type">{event.source_type}</Field>
            <Field label="Source IP" mono>
              {event.source_ip ? (
                <Link className="text-accent hover:underline" to={`/events?source_ip=${event.source_ip}`}>
                  {event.source_ip}
                </Link>
              ) : (
                "—"
              )}
            </Field>
            <Field label="Destination" mono>
              {event.destination_ip
                ? `${event.destination_ip}${event.destination_port ? `:${event.destination_port}` : ""}`
                : "—"}
            </Field>
            <Field label="User">{event.username ?? "—"}</Field>
            <Field label="Service">{event.service ?? "—"}</Field>
            <Field label="Action">{event.action ?? "—"}</Field>
            <Field label="Status">{event.status ?? "—"}</Field>
            <Field label="Bytes Out">{event.bytes_out.toLocaleString()}</Field>
            <Field label="Bytes In">{event.bytes_in.toLocaleString()}</Field>
          </div>

          {event.message && (
            <Field label="Message">
              <span className="font-mono text-[11.5px] text-dim">{event.message}</span>
            </Field>
          )}

          <div>
            <div className="mb-1 flex items-center justify-between text-2xs font-semibold uppercase tracking-[0.06em] text-faint">
              Raw event <CopyButton text={JSON.stringify(event, null, 2)} />
            </div>
            <pre className="max-h-80 overflow-auto rounded border border-line bg-elev p-3 font-mono text-[11px] leading-relaxed text-dim">
              {JSON.stringify(event, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </Drawer>
  );
}
