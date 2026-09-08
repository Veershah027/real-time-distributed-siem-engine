import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

export function Tabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: { id: T; label: ReactNode; count?: number }[];
  active: T;
  onChange: (id: T) => void;
}) {
  return (
    <div role="tablist" className="flex gap-0.5 border-b border-line px-2">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={active === t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "relative flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium transition-colors",
            active === t.id ? "text-ink" : "text-faint hover:text-dim",
          )}
        >
          {t.label}
          {t.count !== undefined && (
            <span className="rounded bg-line px-1 text-[10px] tnum text-dim">{t.count}</span>
          )}
          {active === t.id && (
            <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent" />
          )}
        </button>
      ))}
    </div>
  );
}
