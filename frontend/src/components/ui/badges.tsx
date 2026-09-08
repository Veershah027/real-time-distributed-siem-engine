import { cn } from "@/lib/cn";
import type { AlertStatus, Severity } from "@/types";
import { SEVERITY_META, STATUS_META } from "@/lib/severity";

export function SeverityBadge({ severity, dot }: { severity: Severity; dot?: boolean }) {
  const m = SEVERITY_META[severity] ?? SEVERITY_META.info;
  return (
    <span
      className={cn("chip border", m.bg, m.border, m.text)}
      style={{ color: m.color }}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full" style={{ background: m.color }} />}
      {m.label}
    </span>
  );
}

export function SeverityBar({ severity }: { severity: Severity }) {
  const m = SEVERITY_META[severity] ?? SEVERITY_META.info;
  return <span className="inline-block h-full w-[3px] rounded" style={{ background: m.color }} />;
}

export function StatusBadge({ status }: { status: AlertStatus }) {
  const m = STATUS_META[status] ?? STATUS_META.open;
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold" style={{ color: m.color }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: m.color }} />
      {m.label}
    </span>
  );
}

export function StatusDot({
  state,
  label,
  pulse,
}: {
  state: "up" | "down" | "idle" | "unknown" | "degraded";
  label?: string;
  pulse?: boolean;
}) {
  const color = {
    up: "var(--ok)",
    down: "var(--down)",
    degraded: "var(--warn)",
    idle: "var(--idle)",
    unknown: "var(--idle)",
  }[state];
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={cn("h-2 w-2 rounded-full", pulse && state === "up" && "pulse-dot")}
        style={{ background: color, boxShadow: `0 0 6px ${color}66` }}
      />
      {label && <span className="text-[11px] text-dim">{label}</span>}
    </span>
  );
}

export function Confidence({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "var(--sev-high)" : pct >= 55 ? "var(--sev-medium)" : "var(--text-dim)";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="tnum text-[12px]" style={{ color }}>
        {pct}%
      </span>
      <span className="h-1 w-9 overflow-hidden rounded-full bg-line">
        <span className="block h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </span>
    </span>
  );
}

export function CountPill({ value, tone = "dim" }: { value: number | string; tone?: string }) {
  return (
    <span
      className="inline-flex min-w-[18px] items-center justify-center rounded-full px-1.5 text-[10px] font-semibold tnum"
      style={{ background: `var(--${tone})`, color: tone === "dim" ? "var(--bg)" : "#fff" }}
    >
      {value}
    </span>
  );
}
