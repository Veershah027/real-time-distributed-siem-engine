import { NavLink } from "react-router-dom";
import clsx from "clsx";
import type { ReactNode } from "react";
import { useRealtimeContext } from "@/hooks/realtimeContext";

const NAV = [
  { to: "/", label: "Dashboard", end: true, icon: "▤" },
  { to: "/events", label: "Events", icon: "≋" },
  { to: "/alerts", label: "Alerts", icon: "▲" },
  { to: "/detections", label: "Detection Rules", icon: "◈" },
  { to: "/threats", label: "Threat Intel", icon: "◎" },
  { to: "/simulator", label: "Simulator", icon: "▶" },
  { to: "/system", label: "System", icon: "⚙" },
];

export function Layout({ children }: { children: ReactNode }) {
  const { connected, eps } = useRealtimeContext();
  return (
    <div className="flex h-full">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-base-700 bg-base-850 md:flex">
        <div className="flex items-center gap-2 px-4 py-4">
          <div className="grid h-8 w-8 place-items-center rounded bg-accent-600 font-bold text-white">
            S
          </div>
          <div>
            <div className="text-sm font-bold leading-tight text-slate-100">SIEM Engine</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">SOC Console</div>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 px-2 py-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-base-700 text-white"
                    : "text-slate-400 hover:bg-base-800 hover:text-slate-200",
                )
              }
            >
              <span className="w-4 text-center text-xs opacity-70">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-base-700 px-4 py-3 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span
              className={clsx(
                "h-2 w-2 rounded-full",
                connected ? "bg-emerald-400" : "bg-sev-critical animate-pulse",
              )}
            />
            {connected ? "Realtime connected" : "Reconnecting…"}
          </div>
          <div className="mt-1 tabular-nums">
            {eps != null ? `${eps.toFixed(1)} events/sec` : "— events/sec"}
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-base-700 bg-base-850 px-4 py-2.5 md:hidden">
          <span className="font-bold text-slate-100">SIEM Engine</span>
          <span
            className={clsx(
              "h-2 w-2 rounded-full",
              connected ? "bg-emerald-400" : "bg-sev-critical",
            )}
          />
        </header>
        <nav className="flex gap-1 overflow-x-auto border-b border-base-700 bg-base-850 px-2 py-1 md:hidden">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  "whitespace-nowrap rounded px-2.5 py-1 text-xs font-medium",
                  isActive ? "bg-base-700 text-white" : "text-slate-400",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <main className="min-h-0 flex-1 overflow-auto p-4">{children}</main>
      </div>
    </div>
  );
}
