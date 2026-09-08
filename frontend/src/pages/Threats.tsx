import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "@/services/api";
import { Card, Loading, ErrorState } from "@/components/primitives";
import { HBarChart } from "@/components/charts";

const REP_TONE: Record<string, string> = {
  malicious: "text-sev-critical",
  suspicious: "text-sev-high",
  neutral: "text-slate-300",
  clean: "text-emerald-400",
};

export function Threats() {
  const [minutes, setMinutes] = useState(60);
  const topIps = useQuery({
    queryKey: ["top-ips", minutes, 15],
    queryFn: () => api.topIps(minutes, 15),
    refetchInterval: 15000,
  });
  const eventTypes = useQuery({
    queryKey: ["event-types", minutes],
    queryFn: () => api.eventTypes(minutes),
    refetchInterval: 20000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-400">Window</span>
        <select
          className="input"
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
        >
          <option value={15}>15 minutes</option>
          <option value={60}>1 hour</option>
          <option value={360}>6 hours</option>
          <option value={1440}>24 hours</option>
        </select>
        <span className="text-xs text-slate-500">
          Enrichment is a deterministic synthetic provider (offline). See threat-model.md.
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Top source IPs by event volume" className="h-72">
          <div className="h-full p-2">
            <HBarChart
              data={(topIps.data?.items ?? []).map((t) => ({
                name: t.source_ip,
                value: t.event_count,
              }))}
            />
          </div>
        </Card>
        <Card title="Event-type distribution" className="h-72">
          <div className="h-full p-2">
            <HBarChart
              data={(eventTypes.data?.items ?? []).slice(0, 12).map((t) => ({
                name: t.event_type,
                value: t.count,
              }))}
              color="#a78bfa"
            />
          </div>
        </Card>
      </div>

      <Card title="Top talkers — enriched">
        {topIps.isLoading ? (
          <Loading />
        ) : topIps.isError ? (
          <ErrorState error={topIps.error} />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0">
              <thead>
                <tr>
                  <th className="th">Source IP</th>
                  <th className="th">Events</th>
                  <th className="th">Auth failures</th>
                  <th className="th">Country</th>
                  <th className="th">ASN</th>
                  <th className="th">Category</th>
                  <th className="th">Reputation</th>
                </tr>
              </thead>
              <tbody>
                {(topIps.data?.items ?? []).map((t) => (
                  <tr key={t.source_ip} className="row-hover border-b border-base-750">
                    <td className="td font-mono text-xs text-slate-200">{t.source_ip}</td>
                    <td className="td tabular-nums text-slate-300">{t.event_count}</td>
                    <td
                      className={clsx(
                        "td tabular-nums",
                        t.auth_failures > 0 ? "text-sev-high" : "text-slate-500",
                      )}
                    >
                      {t.auth_failures}
                    </td>
                    <td className="td text-slate-400">
                      {t.enrichment.is_private ? "internal" : (t.enrichment.country ?? "—")}
                    </td>
                    <td className="td text-slate-400">{t.enrichment.asn ?? "—"}</td>
                    <td className="td text-slate-400">{t.enrichment.category ?? "—"}</td>
                    <td
                      className={clsx(
                        "td font-semibold",
                        REP_TONE[t.enrichment.reputation] ?? "text-slate-300",
                      )}
                    >
                      {t.enrichment.reputation} ({t.enrichment.reputation_score})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
