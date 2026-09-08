# SIEM Engine — SOC Dashboard

React 18 + TypeScript + Vite + Tailwind + Recharts + TanStack Query SPA.

```bash
npm ci
npm run dev          # http://localhost:5173  (proxies /api and /ws to :8000)
npm run build        # tsc --noEmit && vite build  ->  dist/
npm run lint
npm run typecheck
npm test             # Vitest
```

## Structure

| Path | Purpose |
|---|---|
| `src/pages/` | Dashboard, Events, Alerts, Detections, Threats, Simulator, System |
| `src/components/` | Layout, EventTable, AlertFeed, AlertDetail, charts, primitives |
| `src/hooks/` | `useRealtime` (single WebSocket) + `RealtimeProvider` context |
| `src/services/api.ts` | typed REST client |
| `src/lib/` | formatting helpers |
| `src/types/` | shared API types |

## Realtime

One WebSocket to `/ws` (configurable via `VITE_WS_URL`), shared across pages via
`RealtimeProvider`. It bridges the backend's Redis pub/sub channels
(`events`, `alerts`, `metrics`) and auto-reconnects with backoff. Query data
(historical lists, metrics, timeseries) comes from REST with short refetch
intervals.

## Production

`Dockerfile` builds the SPA and serves it from nginx on port `8080`, reverse
-proxying `/api` and `/ws` to the `backend` service (same-origin, no CORS).
Build args `VITE_API_BASE_URL` (empty ⇒ same-origin) and `VITE_WS_URL` (`/ws`).
