import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { clockTime } from "@/lib/format";
import { eventTypeLabel, severityColor } from "@/lib/severity";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, Segmented } from "@/components/ui/primitives";
import { DataTable, Pagination, type Column } from "@/components/ui/DataTable";
import { EventStream } from "@/components/events/EventStream";
import { EventDetail } from "@/components/events/EventDetail";
import { Icon } from "@/components/ui/Icon";
import type { SecurityEvent } from "@/types";

const EVENT_TYPES = [
  "authentication_failure",
  "authentication_success",
  "privilege_escalation",
  "http_request",
  "firewall_deny",
  "firewall_allow",
  "connection_attempt",
  "network_flow",
  "db_query",
  "db_error",
  "dns_query",
];
const SEVERITIES = ["critical", "high", "medium", "low", "info"];
const PAGE = 60;

export function LiveEvents() {
  const rt = useRealtime();
  const [params, setParams] = useSearchParams();
  const [mode, setMode] = useState<"live" | "search">(
    params.toString() ? "search" : "live",
  );
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<SecurityEvent | null>(null);

  const filters = useMemo(() => {
    const f: Record<string, string> = {};
    for (const [k, v] of params.entries()) if (v) f[k] = v;
    return f;
  }, [params]);

  const setFilter = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v);
    else next.delete(k);
    setParams(next, { replace: true });
    setOffset(0);
    setMode("search");
  };

  const query = useQuery({
    queryKey: ["events-search", filters, offset],
    queryFn: () => api.events({ ...filters, limit: PAGE, offset }),
    placeholderData: keepPreviousData,
    enabled: mode === "search",
    refetchInterval: mode === "search" ? 10000 : false,
  });

  const activeFilters = Object.entries(filters);

  const columns: Column<SecurityEvent>[] = [
    {
      key: "time",
      header: "Time",
      width: "68px",
      render: (e) => (
        <span className="relative block pl-2 font-mono text-[11px] text-faint">
          <span
            className="absolute inset-y-0 left-0 w-[3px]"
            style={{ background: severityColor(e.severity) }}
          />
          {clockTime(e.timestamp)}
        </span>
      ),
    },
    { key: "src", header: "Source", width: "110px", render: (e) => <span className="text-dim">{e.source}</span> },
    { key: "type", header: "Type", render: (e) => eventTypeLabel(e.event_type) },
    {
      key: "ip",
      header: "Source IP",
      width: "130px",
      render: (e) =>
        e.source_ip ? (
          <button
            className="mono-cell hover:text-accent"
            onClick={(ev) => {
              ev.stopPropagation();
              setFilter("source_ip", e.source_ip!);
            }}
          >
            {e.source_ip}
          </button>
        ) : (
          <span className="text-faint">—</span>
        ),
    },
    { key: "user", header: "User", width: "90px", render: (e) => <span className="text-dim">{e.username ?? "—"}</span> },
    {
      key: "status",
      header: "Status",
      width: "70px",
      render: (e) => <span className="text-[11px] text-faint">{e.status ?? "—"}</span>,
    },
    {
      key: "msg",
      header: "Message",
      render: (e) => (
        <span className="block max-w-md truncate font-mono text-[10.5px] text-faint">
          {e.message ?? "—"}
        </span>
      ),
    },
  ];

  return (
    <div className="flex h-[calc(100vh-var(--topbar-h)-2rem)] flex-col gap-3">
      <PageHeader
        title="Live Events"
        subtitle="Every event ingested by the stream processor"
        actions={
          <Segmented
            value={mode}
            onChange={(v) => {
              setMode(v);
              if (v === "live") setParams(new URLSearchParams(), { replace: true });
            }}
            options={[
              { value: "live", label: "Live Stream" },
              { value: "search", label: "Search / History" },
            ]}
          />
        }
      />

      {mode === "search" && (
        <Panel title="Filters">
          <div className="flex flex-wrap items-center gap-2 p-2.5">
            <input
              className="input w-48"
              placeholder="search message text"
              defaultValue={filters.q ?? ""}
              onKeyDown={(e) => e.key === "Enter" && setFilter("q", (e.target as HTMLInputElement).value)}
            />
            <input
              className="input w-40"
              placeholder="source IP"
              defaultValue={filters.source_ip ?? ""}
              onKeyDown={(e) =>
                e.key === "Enter" && setFilter("source_ip", (e.target as HTMLInputElement).value)
              }
            />
            <input
              className="input w-32"
              placeholder="username"
              defaultValue={filters.username ?? ""}
              onKeyDown={(e) =>
                e.key === "Enter" && setFilter("username", (e.target as HTMLInputElement).value)
              }
            />
            <select
              className="input"
              value={filters.event_type ?? ""}
              onChange={(e) => setFilter("event_type", e.target.value)}
            >
              <option value="">all types</option>
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {eventTypeLabel(t)}
                </option>
              ))}
            </select>
            <select
              className="input"
              value={filters.severity ?? ""}
              onChange={(e) => setFilter("severity", e.target.value)}
            >
              <option value="">all severities</option>
              {SEVERITIES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
            {activeFilters.length > 0 && (
              <button
                className="btn btn-xs btn-ghost"
                onClick={() => {
                  setParams(new URLSearchParams(), { replace: true });
                  setOffset(0);
                }}
              >
                Clear ({activeFilters.length})
              </button>
            )}
          </div>
        </Panel>
      )}

      <Panel
        title={
          mode === "live"
            ? "Live Event Stream"
            : `Search Results${query.data ? ` — ${query.data.total.toLocaleString()}` : ""}`
        }
        className="min-h-0 flex-1"
        actions={
          mode === "search" &&
          activeFilters.map(([k, v]) => (
            <span key={k} className="chip border border-line bg-elev text-dim">
              {k}: {v}
              <button onClick={() => setFilter(k, "")} aria-label={`remove ${k}`}>
                <Icon.close size={10} />
              </button>
            </span>
          ))
        }
      >
        {mode === "live" ? (
          <EventStream
            events={rt.events}
            paused={rt.paused}
            onPause={rt.setPaused}
            onClear={rt.clearEvents}
            liveCount={rt.eventCount}
          />
        ) : query.isLoading ? (
          <Loading />
        ) : query.isError ? (
          <ErrorState error={query.error} retry={() => query.refetch()} />
        ) : (
          <div className="flex h-full flex-col">
            <div className="min-h-0 flex-1 overflow-auto">
              <DataTable
                columns={columns}
                rows={query.data?.items ?? []}
                rowKey={(e) => e.event_id}
                onRowClick={setSelected}
                dense
                empty="No events match these filters"
              />
            </div>
            <Pagination
              offset={offset}
              limit={PAGE}
              total={query.data?.total ?? 0}
              onChange={setOffset}
            />
          </div>
        )}
      </Panel>

      <EventDetail event={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
