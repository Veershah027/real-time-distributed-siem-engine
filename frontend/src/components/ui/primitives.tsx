import { useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Icon } from "./Icon";

/* ---------- Panel ---------- */
export function Panel({
  title,
  actions,
  children,
  className,
  bodyClassName,
  scroll,
}: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  scroll?: boolean;
}) {
  return (
    <section className={cn("panel flex min-h-0 flex-col", className)}>
      {(title || actions) && (
        <header className="panel-head">
          <span className="panel-title truncate">{title}</span>
          {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
        </header>
      )}
      <div className={cn("min-h-0 flex-1", scroll && "overflow-auto", bodyClassName)}>{children}</div>
    </section>
  );
}

/* ---------- StatCard ---------- */
export function StatCard({
  label,
  value,
  sub,
  tone = "default",
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "default" | "critical" | "high" | "ok" | "warn";
  icon?: ReactNode;
}) {
  const toneText = {
    default: "text-ink",
    critical: "text-sev-critical",
    high: "text-sev-high",
    ok: "text-ok",
    warn: "text-warn",
  }[tone];
  return (
    <div className="panel px-3.5 py-3">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-semibold uppercase tracking-[0.07em] text-faint">
          {label}
        </span>
        {icon && <span className="text-faint">{icon}</span>}
      </div>
      <div className={cn("mt-1.5 text-[22px] font-semibold leading-none tnum", toneText)}>{value}</div>
      {sub !== undefined && <div className="mt-1.5 text-2xs text-faint">{sub}</div>}
    </div>
  );
}

/* ---------- Field (label / value) ---------- */
export function Field({ label, children, mono }: { label: string; children: ReactNode; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <div className="text-2xs font-semibold uppercase tracking-[0.06em] text-faint">{label}</div>
      <div className={cn("mt-0.5 break-words text-[12.5px] text-ink", mono && "font-mono text-[11.5px]")}>
        {children}
      </div>
    </div>
  );
}

/* ---------- states ---------- */
export function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: ReactNode }) {
  return (
    <div className="flex h-full min-h-[120px] flex-col items-center justify-center gap-1.5 px-6 py-10 text-center">
      {icon && <div className="text-faint opacity-60">{icon}</div>}
      <div className="text-[12.5px] font-medium text-dim">{title}</div>
      {hint && <div className="max-w-xs text-2xs text-faint">{hint}</div>}
    </div>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex h-full min-h-[120px] items-center justify-center gap-2 py-10 text-xs text-faint">
      <span className="h-3 w-3 animate-spin rounded-full border-[1.5px] border-line-strong border-t-accent" />
      {label}…
    </div>
  );
}

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="m-3 rounded border border-[var(--sev-critical)]/40 bg-[var(--sev-critical)]/8 p-3 text-xs">
      <div className="font-semibold text-sev-critical">Request failed</div>
      <div className="mt-1 font-mono text-[11px] text-dim">{msg}</div>
      {retry && (
        <button className="btn btn-xs mt-2" onClick={retry}>
          <Icon.refresh size={12} /> Retry
        </button>
      )}
    </div>
  );
}

/* ---------- controls ---------- */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  size = "sm",
}: {
  value: T;
  options: { value: T; label: ReactNode }[];
  onChange: (v: T) => void;
  size?: "sm" | "xs";
}) {
  return (
    <div className="inline-flex rounded border border-line-strong bg-elev p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-[4px] font-medium transition-colors",
            size === "xs" ? "px-2 py-0.5 text-2xs" : "px-2.5 py-1 text-[11px]",
            value === o.value ? "bg-panel-3 text-ink" : "text-faint hover:text-dim",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-4 w-7 shrink-0 rounded-full transition-colors",
        checked ? "bg-accent" : "bg-line-strong",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 h-3 w-3 rounded-full bg-white transition-transform",
          checked ? "translate-x-3.5" : "translate-x-0.5",
        )}
      />
    </button>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded border border-line-strong bg-elev px-1.5 py-0.5 font-mono text-[10px] text-dim">
      {children}
    </kbd>
  );
}

export function CopyButton({ text, className }: { text: string; className?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      className={cn("btn-ghost inline-flex h-5 w-5 items-center justify-center rounded text-faint hover:text-dim", className)}
      title="Copy"
      onClick={async (e) => {
        e.stopPropagation();
        try {
          await navigator.clipboard.writeText(text);
          setDone(true);
          setTimeout(() => setDone(false), 1200);
        } catch {
          /* clipboard unavailable */
        }
      }}
    >
      {done ? <Icon.check size={12} /> : <Icon.copy size={12} />}
    </button>
  );
}

export function ProgressBar({ value, tone = "accent" }: { value: number; tone?: string }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-line">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: `var(--${tone})` }}
      />
    </div>
  );
}
