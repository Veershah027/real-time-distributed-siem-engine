import { NavLink } from "react-router-dom";
import { cn } from "@/lib/cn";
import { Icon } from "@/components/ui/Icon";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { NAV } from "./nav";

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { conn } = useRealtime();

  return (
    <nav className="flex h-full w-[var(--sidebar-w)] shrink-0 flex-col border-r border-line bg-bg">
      <div className="flex items-center gap-2.5 px-4 py-3.5">
        <div className="grid h-7 w-7 place-items-center rounded-md border border-accent/40 bg-accent/10 text-accent">
          <Icon.shield size={16} />
        </div>
        <div className="leading-tight">
          <div className="text-[12.5px] font-semibold tracking-tight text-ink">SIEM Command</div>
          <div className="text-2xs uppercase tracking-[0.14em] text-faint">Operations Center</div>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-2 pb-4">
        {NAV.map((group) => (
          <div key={group.label}>
            <div className="px-2.5 pb-1 pt-1 text-[9.5px] font-semibold uppercase tracking-[0.12em] text-faint">
              {group.label}
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const IconCmp = Icon[item.icon];
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[12.5px] font-medium transition-colors",
                        isActive
                          ? "bg-accent/12 text-ink"
                          : "text-dim hover:bg-panel-2 hover:text-ink",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <IconCmp size={15} className={isActive ? "text-accent" : "text-faint"} />
                        {item.label}
                      </>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-line px-3 py-2.5 text-2xs">
        <div className="flex items-center gap-2 text-dim">
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              conn === "online" ? "bg-ok pulse-dot" : "bg-down",
            )}
          />
          {conn === "online" ? "Realtime stream active" : "Stream reconnecting…"}
        </div>
      </div>
    </nav>
  );
}
