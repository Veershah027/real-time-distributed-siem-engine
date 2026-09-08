import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card, Loading, ErrorState } from "@/components/primitives";
import { EventTable } from "@/components/EventTable";

const EVENT_TYPES = [
  "authentication_failure",
  "authentication_success",
  "http_request",
  "firewall_deny",
  "firewall_allow",
  "db_query",
  "db_error",
  "privilege_escalation",
  "network_flow",
  "dns_query",
  "connection_attempt",
];
const SEVERITIES = ["critical", "high", "medium", "low", "info"];
const PAGE = 50;

export function Events() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");

  const query = useQuery({
    queryKey: ["events", filters, offset, search],
    queryFn: () =>
      api.events({ ...filters, q: search || undefined, limit: PAGE, offset }),
    placeholderData: keepPreviousData,
    refetchInterval: 8000,
  });

  const update = (k: string, v: string) => {
    setOffset(0);
    setFilters((f) => {
      const next = { ...f };
      if (v) next[k] = v;
      else delete next[k];
      return next;
    });
  };

  const total = query.data?.total ?? 0;

  return (
    <Card
      title={`Events${total ? ` — ${total.toLocaleString()} match` : ""}`}
      action={
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="input w-40"
            placeholder="search message…"
            value={search}
            onChange={(e) => {
              setOffset(0);
              setSearch(e.target.value);
            }}
          />
          <input
            className="input w-36"
            placeholder="source IP"
            onChange={(e) => update("source_ip", e.target.value.trim())}
          />
          <select
            className="input"
            value={filters.event_type ?? ""}
            onChange={(e) => update("event_type", e.target.value)}
          >
            <option value="">all types</option>
            {EVENT_TYPES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
          <select
            className="input"
            value={filters.severity ?? ""}
            onChange={(e) => update("severity", e.target.value)}
          >
            <option value="">all severities</option>
            {SEVERITIES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      }
    >
      {query.isLoading ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState error={query.error} />
      ) : (
        <>
          <div className="max-h-[calc(100vh-16rem)] overflow-auto">
            <EventTable events={query.data?.items ?? []} />
          </div>
          <div className="flex items-center justify-between border-t border-base-700 px-4 py-2 text-xs text-slate-400">
            <span>
              {offset + 1}–{Math.min(offset + PAGE, total)} of {total.toLocaleString()}
            </span>
            <div className="flex gap-2">
              <button
                className="btn-ghost"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
              >
                Prev
              </button>
              <button
                className="btn-ghost"
                disabled={offset + PAGE >= total}
                onClick={() => setOffset(offset + PAGE)}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}
