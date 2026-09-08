import { createContext, useContext, type ReactNode } from "react";
import { useRealtime } from "./useRealtime";

type Ctx = ReturnType<typeof useRealtime>;

const RealtimeContext = createContext<Ctx | null>(null);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const value = useRealtime();
  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtimeContext(): Ctx {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error("useRealtimeContext must be used within RealtimeProvider");
  return ctx;
}
