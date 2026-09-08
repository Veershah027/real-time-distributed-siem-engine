import { useRealtime } from "@/realtime/RealtimeProvider";

export function ConnectionBanner() {
  const { conn, retries } = useRealtime();
  if (conn === "online" || conn === "connecting") return null;

  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 border-b border-[var(--sev-high)]/40 bg-[var(--sev-high)]/10 px-4 py-1.5 text-[11.5px] font-medium text-sev-high"
    >
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[var(--sev-high)]" />
      Real-time connection lost — attempting to reconnect
      {retries > 1 ? ` (attempt ${retries})` : ""}…
    </div>
  );
}
