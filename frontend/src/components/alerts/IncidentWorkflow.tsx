import { cn } from "@/lib/cn";
import type { AlertStatus } from "@/types";
import { NEXT_STATES, STATUS_META, WORKFLOW } from "@/lib/severity";
import { Icon } from "@/components/ui/Icon";

export function IncidentWorkflow({
  status,
  onChange,
  pending,
}: {
  status: AlertStatus;
  onChange: (s: AlertStatus) => void;
  pending: boolean;
}) {
  const terminalFP = status === "false_positive";
  const activeIdx = WORKFLOW.indexOf(status);
  const next = NEXT_STATES[status];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1">
        {WORKFLOW.map((s, i) => {
          const done = !terminalFP && activeIdx >= i && activeIdx !== -1;
          const current = s === status;
          return (
            <div key={s} className="flex flex-1 items-center gap-1">
              <div className="flex flex-col items-center gap-1">
                <span
                  className={cn(
                    "grid h-5 w-5 place-items-center rounded-full border text-[10px] font-bold",
                    current
                      ? "border-transparent text-white"
                      : done
                        ? "border-transparent text-white"
                        : "border-line-strong text-faint",
                  )}
                  style={
                    current || done ? { background: STATUS_META[s].color } : undefined
                  }
                >
                  {done && !current ? <Icon.check size={11} /> : i + 1}
                </span>
                <span
                  className={cn(
                    "text-[9.5px] font-semibold uppercase tracking-wide",
                    current ? "text-ink" : "text-faint",
                  )}
                >
                  {STATUS_META[s].label}
                </span>
              </div>
              {i < WORKFLOW.length - 1 && (
                <span
                  className={cn("h-px flex-1", done ? "bg-[var(--accent)]" : "bg-line-strong")}
                />
              )}
            </div>
          );
        })}
      </div>

      {terminalFP && (
        <div className="rounded border border-line bg-elev px-2.5 py-1.5 text-[11px] text-idle">
          Marked as false positive.
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {next.map((s) => (
          <button
            key={s}
            disabled={pending}
            onClick={() => onChange(s)}
            className={cn(
              "btn btn-xs",
              s === "resolved" && "btn-primary",
              s === "false_positive" && "btn-danger",
            )}
          >
            {s === "open" ? "Re-open" : `Mark ${STATUS_META[s].label}`}
          </button>
        ))}
      </div>
    </div>
  );
}
