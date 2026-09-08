import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import { num } from "@/lib/format";
import { useTimeRange } from "@/hooks/useTimeRange";
import { PageHeader } from "@/components/shell/AppShell";
import { Panel, Loading, ErrorState } from "@/components/ui/primitives";
import { DataTable, type Column } from "@/components/ui/DataTable";
import type { TopIp } from "@/types";

const REP_TONE: Record<string, string> = {
  malicious: "text-sev-critical",
  suspicious: "text-sev-high",
  neutral: "text-dim",
  clean: "text-ok",
};

export function SourceAnalytics() {
  const navigate = useNavigate();
  const range = useTimeRange();
  const ipsQ = useQuery({
    queryKey: ["top-ips-full", range.minutes],
    queryFn: () => api.topIps(range.minutes, 25),
    refetchInterval: 20000,
  });
  const hostsQ = useQuery({
    queryKey: ["top-hosts", range.minutes],
    queryFn: () => api.topHosts(range.minutes, 20),
    refetchInterval: 20000,
  });

  const ipColumns: Column<TopIp>[] = [
    {
      key: "ip",
      header: "Source IP",
      render: (t) => (
        <button className="mono-cell hover:text-accent" onClick={() => navigate(`/events?source_ip=${t.source_ip}`)}>
          {t.source_ip}
        </button>
      ),
    },
    { key: "ev", header: "Events", align: "right", render: (t) => <span className="tnum text-dim">{num(t.event_count)}</span> },
    {
      key: "af",
      header: "Auth Fails",
      align: "right",
      render: (t) => (
        <span className={cn("tnum", t.auth_failures ? "text-sev-high" : "text-faint")}>
          {t.auth_failures}
        </span>
      ),
    },
    {
      key: "loc",
      header: "Geo / ASN",
      render: (t) =>
        t.enrichment.is_private ? (
          <span className="text-faint">internal</span>
        ) : (
          <span className="text-dim">
            {t.enrichment.country ?? "—"} · <span className="font-mono text-2xs">{t.enrichment.asn ?? "—"}</span>
          </span>
        ),
    },
    { key: "cat", header: "Category", render: (t) => <span className="text-dim">{t.enrichment.category ?? "—"}</span> },
    {
      key: "rep",
      header: "Reputation",
      render: (t) => (
        <span className={cn("font-semibold", REP_TONE[t.enrichment.reputation] ?? "text-dim")}>
          {t.enrichment.reputation} ({t.enrichment.reputation_score})
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Source Analytics"
        subtitle={`Top talkers over the last ${range.label} · enrichment is a deterministic offline provider`}
      />

      <Panel title="Top Source IPs — enriched">
        {ipsQ.isLoading ? (
          <Loading />
        ) : ipsQ.isError ? (
          <ErrorState error={ipsQ.error} retry={() => ipsQ.refetch()} />
        ) : (
          <DataTable
            columns={ipColumns}
            rows={ipsQ.data?.items ?? []}
            rowKey={(t) => t.source_ip}
            dense
            empty="No source IP activity in this window"
          />
        )}
      </Panel>

      <div className="grid gap-3 lg:grid-cols-2">
        <Panel title="Top Event Sources (hosts)" bodyClassName="max-h-80 overflow-auto">
          {hostsQ.data && (
            <DataTable
              dense
              rows={hostsQ.data.top_event_sources}
              rowKey={(h) => h.host}
              columns={[
                { key: "h", header: "Host", render: (h) => h.host },
                { key: "t", header: "Type", render: (h) => <span className="text-dim">{h.source_type}</span> },
                { key: "e", header: "Events", align: "right", render: (h) => <span className="tnum text-dim">{num(h.event_count)}</span> },
                {
                  key: "hi",
                  header: "High-sev",
                  align: "right",
                  render: (h) => (
                    <span className={cn("tnum", h.high_severity_events ? "text-sev-high" : "text-faint")}>
                      {h.high_severity_events}
                    </span>
                  ),
                },
              ]}
              empty="No data"
            />
          )}
        </Panel>
        <Panel title="Top Attacked Hosts (by alert)" bodyClassName="max-h-80 overflow-auto">
          {hostsQ.data && (
            <DataTable
              dense
              rows={hostsQ.data.top_attacked_hosts}
              rowKey={(h) => h.host}
              columns={[
                { key: "h", header: "Host", render: (h) => h.host },
                { key: "a", header: "Alerts", align: "right", render: (h) => <span className="tnum text-sev-high">{h.alert_count}</span> },
                { key: "c", header: "Critical", align: "right", render: (h) => <span className="tnum text-sev-critical">{h.critical_alerts}</span> },
                { key: "e", header: "Events", align: "right", render: (h) => <span className="tnum text-dim">{num(h.event_count)}</span> },
              ]}
              empty="No host alerts in this window"
            />
          )}
        </Panel>
      </div>
    </div>
  );
}
