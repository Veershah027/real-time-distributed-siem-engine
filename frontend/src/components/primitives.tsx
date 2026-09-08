import clsx from "clsx";
import type { ReactNode } from "react";
import type { Severity } from "@/types";

const SEV_STYLES: Record<Severity, string> = {
  critical: "bg-sev-critical/15 text-sev-critical border-sev-critical/40",
  high: "bg-sev-high/15 text-sev-high border-sev-high/40",
  medium: "bg-sev-medium/15 text-sev-medium border-sev-medium/40",
  low: "bg-sev-low/15 text-sev-low border-sev-low/40",
  info: "bg-sev-info/15 text-slate-300 border-sev-info/40",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide",
        SEV_STYLES[severity] ?? SEV_STYLES.info,
      )}
    >
      {severity}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  open: "text-sev-high",
  acknowledged: "text-accent",
  resolved: "text-emerald-400",
  false_positive: "text-slate-400",
};

export function StatusPill({ status }: { status: string }) {
  return (
    <span className={clsx("text-xs font-semibold", STATUS_STYLES[status] ?? "text-slate-300")}>
      {status.replace("_", " ")}
    </span>
  );
}

export function StatCard({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "default" | "critical" | "high" | "good";
}) {
  const toneClass = {
    default: "text-slate-100",
    critical: "text-sev-critical",
    high: "text-sev-high",
    good: "text-emerald-400",
  }[tone];
  return (
    <div className="card card-pad">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </div>
      <div className={clsx("mt-1 text-2xl font-bold tabular-nums", toneClass)}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1 py-14 text-center">
      <div className="text-sm font-medium text-slate-400">{title}</div>
      {hint && <div className="max-w-sm text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-14 text-sm text-slate-500">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-600 border-t-accent" />
      {label}
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="m-4 rounded-md border border-sev-critical/40 bg-sev-critical/10 p-3 text-sm text-sev-critical">
      Failed to load: {msg}
    </div>
  );
}

export function Card({
  title,
  action,
  children,
  className,
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("card flex flex-col", className)}>
      {title && (
        <div className="flex items-center justify-between border-b border-base-700 px-4 py-2.5">
          <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
          {action}
        </div>
      )}
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  );
}
