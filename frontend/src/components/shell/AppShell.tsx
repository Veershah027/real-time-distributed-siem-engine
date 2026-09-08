import { useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { cn } from "@/lib/cn";
import { Icon } from "@/components/ui/Icon";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { ConnectionBanner } from "./ConnectionBanner";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileNav, setMobileNav] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    setMobileNav(false);
  }, [pathname]);

  return (
    <div className="flex h-full">
      {/* desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar />
      </div>

      {/* mobile drawer */}
      {mobileNav && (
        <div className="fixed inset-0 z-50 flex md:hidden" style={{ background: "var(--overlay)" }}>
          <div onClick={(e) => e.stopPropagation()} className="h-full">
            <Sidebar onNavigate={() => setMobileNav(false)} />
          </div>
          <button
            className="flex-1"
            aria-label="Close navigation"
            onClick={() => setMobileNav(false)}
          />
          <button
            className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded bg-panel-2 text-dim"
            onClick={() => setMobileNav(false)}
          >
            <Icon.close size={16} />
          </button>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setMobileNav(true)} />
        <ConnectionBanner />
        <main className={cn("min-h-0 flex-1 overflow-y-auto bg-bg p-3 sm:p-4")}>{children}</main>
      </div>
    </div>
  );
}

/** Standard page heading + optional right-side actions. */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[15px] font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-0.5 text-xs text-faint">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
