import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { relTime } from "@/lib/format";
import { STATUS_META } from "@/lib/severity";
import { useRealtime } from "@/realtime/RealtimeProvider";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState, Segmented, StatCard } from "@/components/ui/primitives";
import { DataTable, Pagination, type Column } from "@/components/ui/DataTable";
import { Confidence, SeverityBadge, StatusBadge } from "@/components/ui/badges";
import { AlertInvestigation } from "@/components/alerts/AlertInvestigation";
import type { Alert } from "@/types";

const STATUSES = ["open", "acknowledged", "investigating", "resolved", "false_positive"];
const SEVERITIES = ["critical", "high", "medium", "low"];
const PAGE = 30;

export function Alerts() {
  const navigate = useNavigate();
  const { alertId } = useParams();
  const rt = useRealtime();
  const [statusF, setStatusF] = useState("");
  const [sevF, setSevF] = useState("");
  const [offset, setOffset] = useState(0);
  const [view, setView] = useState<"active" | "all">("active");

  useEffect(() => {
    if (view === "active" && !statusF) return;
  }, [view, statusF]);

  const metricsQ = useQuery({ queryKey: ["metrics"], queryFn: api.metrics, refetchInterval: 5000 });
  const query = useQuery({
    queryKey: ["alerts", statusF, sevF, offset, view],
    queryFn: () =>
      api.alerts({
        status: statusF || undefined,
        severity: sevF || undefined,
        limit: PAGE,
        offset,
      }),
    placeholderData: keepPreviousData,
    refetchInterval: 5000,
  });

  const m = metricsQ.data;
  const rows = (query.data?.items ?? []).filter((a) =>
    view === "active"
      ? ["open", "acknowledged", "investigating"].includes(a.status) || statusF
      : true,
  );
  const total = view === "active" && !statusF ? (m?.active_alerts_total ?? rows.length) : query.data?.total ?? 0;

  const columns: Column<Alert>[] = [
    { key: "sev", header: "Severity", width: "92px", render: (a) => <SeverityBadge severity={a.severity} /> },
    {
      key: "rule",
      header: "Rule",
      width: "88px",
      render: (a) => <span className="mono-cell">{a.rule_id}</span>,
    },
    { key: "title", header: "Title", render: (a) => <span className="text-ink">{a.title}</span> },
    {
      key: "src",
      header: "Source",
      width: "120px",
      render: (a) => <span className="mono-cell">{a.source_ip ?? "—"}</span>,
    },
    { key: "host", header: "Target", width: "110px", render: (a) => <span className="text-dim">{a.affected_host ?? "—"}</span> },
    { key: "ev", header: "Events", width: "62px", align: "right", render: (a) => <span className="tnum text-dim">{a.event_count}</span> },
    { key: "conf", header: "Confidence", width: "110px", render: (a) => <Confidence value={a.confidence} /> },
    { key: "status", header: "Status", width: "120px", render: (a) => <StatusBadge status={a.status} /> },
    {
      key: "seen",
      header: "Last Seen",
      width: "84px",
      render: (a) => <span className="text-2xs text-faint">{relTime(a.last_seen)}</span>,
    },
  ];

  return (
    <div className="flex h-[calc(100vh-var(--topbar-h)-2rem)] flex-col gap-3">
      <PageHeader
        title="Alert Queue"
        subtitle="Correlated detections — click a row to open the investigation view"
        actions={
          <Segmented
            value={view}
            onChange={(v) => {
              setView(v);
              setOffset(0);
              if (v === "active") setStatusF("");
            }}
            options={[
              { value: "active", label: "Active Queue" },
              { value: "all", label: "All Alerts" },
            ]}
          />
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatCard label="Open" value={m ? m.active_alerts_total - m.acknowledged_alerts - m.investigating_alerts : "—"} tone="high" />
        <StatCard label="Acknowledged" value={m?.acknowledged_alerts ?? "—"} />
        <StatCard label="Investigating" value={m?.investigating_alerts ?? "—"} tone="warn" />
        <StatCard label="Resolved" value={m?.resolved_alerts ?? "—"} tone="ok" />
        <StatCard label="False Positive" value={m?.false_positive_alerts ?? "—"} />
      </div>

      <Panel
        title="Alerts"
        className="min-h-0 flex-1"
        actions={
          <div className="flex gap-1.5">
            <select className="input btn-xs h-7" value={statusF} onChange={(e) => { setStatusF(e.target.value); setOffset(0); }}>
              <option value="">{view === "active" ? "active statuses" : "all statuses"}</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_META[s as keyof typeof STATUS_META].label}
                </option>
              ))}
            </select>
            <select className="input btn-xs h-7" value={sevF} onChange={(e) => { setSevF(e.target.value); setOffset(0); }}>
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
          <ErrorState error={query.error} retry={() => query.refetch()} />
        ) : (
          <div className="flex h-full flex-col">
            <div className="min-h-0 flex-1 overflow-auto">
              <DataTable
                columns={columns}
                rows={rows}
                rowKey={(a) => a.alert_id}
                onRowClick={(a) => navigate(`/alerts/${a.alert_id}`)}
                activeKey={alertId}
                flashFirst={rt.lastAlert ? rows[0]?.alert_id === rt.lastAlert.alert_id : false}
                dense
                empty="No alerts match the current filter"
              />
            </div>
            <Pagination offset={offset} limit={PAGE} total={total} onChange={setOffset} />
          </div>
        )}
      </Panel>

      {alertId && <AlertInvestigation alertId={alertId} onClose={() => navigate("/alerts")} />}
    </div>
  );
}
