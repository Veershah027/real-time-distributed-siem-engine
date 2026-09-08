import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { Alert, PerfSample, SecurityEvent } from "@/types";

export type ConnState = "connecting" | "online" | "reconnecting" | "offline";

interface RealtimeValue {
  conn: ConnState;
  retries: number;
  events: SecurityEvent[];
  alerts: Alert[];
  lastAlert: Alert | null;
  liveMetrics: Partial<PerfSample> | null;
  paused: boolean;
  setPaused: (v: boolean) => void;
  clearEvents: () => void;
  eventCount: number;
}

const RealtimeContext = createContext<RealtimeValue | null>(null);

const WS_URL = (() => {
  const configured = import.meta.env.VITE_WS_URL;
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  if (!configured) return `${scheme}://${location.host}/ws`;
  if (configured.startsWith("ws")) return configured;
  return `${scheme}://${location.host}${configured.startsWith("/") ? "" : "/"}${configured}`;
})();

const MAX_EVENTS = 250;
const MAX_ALERTS = 80;

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [conn, setConn] = useState<ConnState>("connecting");
  const [retries, setRetries] = useState(0);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<Partial<PerfSample> | null>(null);
  const [paused, setPausedState] = useState(false);
  const [eventCount, setEventCount] = useState(0);

  const pausedRef = useRef(paused);
  pausedRef.current = paused;
  const bufferRef = useRef<SecurityEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const setPaused = useCallback((v: boolean) => {
    setPausedState(v);
    if (!v && bufferRef.current.length) {
      setEvents((prev) => [...bufferRef.current, ...prev].slice(0, MAX_EVENTS));
      bufferRef.current = [];
    }
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    bufferRef.current = [];
  }, []);

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      if (disposed) return;
      setConn((c) => (c === "offline" || c === "reconnecting" ? "reconnecting" : "connecting"));
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConn("online");
        retryRef.current = 0;
        setRetries(0);
      };
      ws.onclose = () => {
        if (disposed) return;
        setConn("reconnecting");
        const n = retryRef.current++;
        setRetries(n + 1);
        const delay = Math.min(1000 * 2 ** n, 15000);
        timer = setTimeout(() => {
          setConn("offline");
          connect();
        }, delay);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (ev) => {
        let msg: { type: string; data: unknown };
        try {
          msg = JSON.parse(ev.data);
        } catch {
          return;
        }
        if (msg.type === "events") {
          const e = msg.data as SecurityEvent;
          setEventCount((c) => c + 1);
          if (pausedRef.current) {
            bufferRef.current = [e, ...bufferRef.current].slice(0, MAX_EVENTS);
          } else {
            setEvents((prev) => [e, ...prev].slice(0, MAX_EVENTS));
          }
        } else if (msg.type === "alerts") {
          const a = msg.data as Alert;
          setLastAlert(a);
          setAlerts((prev) =>
            [a, ...prev.filter((x) => x.alert_id !== a.alert_id)].slice(0, MAX_ALERTS),
          );
        } else if (msg.type === "metrics") {
          setLiveMetrics(msg.data as Partial<PerfSample>);
        }
      };
    };

    connect();
    return () => {
      disposed = true;
      clearTimeout(timer);
      wsRef.current?.close();
    };
  }, []);

  const value = useMemo<RealtimeValue>(
    () => ({
      conn,
      retries,
      events,
      alerts,
      lastAlert,
      liveMetrics,
      paused,
      setPaused,
      clearEvents,
      eventCount,
    }),
    [conn, retries, events, alerts, lastAlert, liveMetrics, paused, setPaused, clearEvents, eventCount],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtime(): RealtimeValue {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error("useRealtime must be used within RealtimeProvider");
  return ctx;
}
