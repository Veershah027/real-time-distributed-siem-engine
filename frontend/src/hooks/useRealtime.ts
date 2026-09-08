import { useEffect, useRef, useState } from "react";
import type { Alert, SecurityEvent } from "@/types";

type WsMessage =
  | { type: "connected"; channels: string[] }
  | { type: "events"; data: SecurityEvent }
  | { type: "alerts"; data: Alert }
  | { type: "metrics"; data: Record<string, number> };

function resolveWsUrl(): string {
  const configured = import.meta.env.VITE_WS_URL;
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  if (!configured) return `${scheme}://${location.host}/ws`;
  if (configured.startsWith("ws://") || configured.startsWith("wss://")) return configured;
  // relative path like "/ws" -> resolve against current origin
  return `${scheme}://${location.host}${configured.startsWith("/") ? "" : "/"}${configured}`;
}
const WS_URL = resolveWsUrl();

interface RealtimeState {
  connected: boolean;
  events: SecurityEvent[];
  alerts: Alert[];
  eps: number | null;
  lastAlert: Alert | null;
}

const MAX_EVENTS = 120;
const MAX_ALERTS = 60;

export function useRealtime(): RealtimeState {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [eps, setEps] = useState<number | null>(null);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;

    const connect = () => {
      if (disposed) return;
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryRef.current = 0;
      };
      ws.onclose = () => {
        setConnected(false);
        const delay = Math.min(1000 * 2 ** retryRef.current++, 15000);
        timer = setTimeout(connect, delay);
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (ev) => {
        let msg: WsMessage;
        try {
          msg = JSON.parse(ev.data);
        } catch {
          return;
        }
        if (msg.type === "events") {
          setEvents((prev) => [msg.data, ...prev].slice(0, MAX_EVENTS));
        } else if (msg.type === "alerts") {
          setLastAlert(msg.data);
          setAlerts((prev) => {
            const without = prev.filter((a) => a.alert_id !== msg.data.alert_id);
            return [msg.data, ...without].slice(0, MAX_ALERTS);
          });
        } else if (msg.type === "metrics" && typeof msg.data.events_per_second === "number") {
          setEps(msg.data.events_per_second);
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

  return { connected, events, alerts, eps, lastAlert };
}
