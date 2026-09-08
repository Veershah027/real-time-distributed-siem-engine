import { useEffect, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { Icon } from "./Icon";

export function Drawer({
  open,
  onClose,
  title,
  children,
  width = "max-w-2xl",
}: {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
  width?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      style={{ background: "var(--overlay)" }}
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          "flex h-full w-full flex-col border-l border-line-strong bg-panel shadow-2xl sm:w-[92vw]",
          width,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex shrink-0 items-center justify-between border-b border-line px-4 py-2.5">
          <div className="min-w-0 text-[12px] font-semibold uppercase tracking-[0.06em] text-dim">
            {title}
          </div>
          <button
            className="btn-ghost inline-flex h-7 w-7 items-center justify-center rounded text-faint hover:text-ink"
            onClick={onClose}
            aria-label="Close"
          >
            <Icon.close size={15} />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
