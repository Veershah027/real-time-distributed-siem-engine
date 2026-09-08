import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { Card, Loading, ErrorState, SeverityBadge } from "@/components/primitives";

export function Detections() {
  const query = useQuery({ queryKey: ["detections"], queryFn: api.detections });

  if (query.isLoading) return <Loading />;
  if (query.isError) return <ErrorState error={query.error} />;

  const rules = query.data?.rules ?? [];
  const byCategory = rules.reduce<Record<string, typeof rules>>((acc, r) => {
    (acc[r.category] ??= []).push(r);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">
        {rules.length} detectors loaded. Deterministic rules are the source of truth; the
        anomaly / ML entries are advisory. Thresholds are configurable via environment
        variables — see <span className="font-mono text-slate-300">docs/detection-rules.md</span>.
      </p>
      {Object.entries(byCategory).map(([category, items]) => (
        <Card key={category} title={category.toUpperCase()}>
          <div className="divide-y divide-base-750">
            {items.map((r) => (
              <div key={r.rule_id} className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-slate-400">{r.rule_id}</span>
                  <span className="font-medium text-slate-100">{r.name}</span>
                  <SeverityBadge severity={r.default_severity} />
                  <span className="rounded bg-base-700 px-1.5 py-0.5 text-[10px] uppercase text-slate-400">
                    {r.kind}
                  </span>
                  <span
                    className={
                      r.enabled
                        ? "ml-auto text-xs text-emerald-400"
                        : "ml-auto text-xs text-slate-500"
                    }
                  >
                    {r.enabled ? "enabled" : "disabled"}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{r.description}</p>
                {Object.keys(r.parameters ?? {}).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(r.parameters).map(([k, v]) => (
                      <span
                        key={k}
                        className="rounded border border-base-700 bg-base-850 px-2 py-0.5 font-mono text-[11px] text-slate-400"
                      >
                        {k}={JSON.stringify(v)}
                      </span>
                    ))}
                  </div>
                )}
                {r.mitre_attack?.length > 0 && (
                  <div className="mt-2 text-[11px] text-slate-500">
                    MITRE ATT&CK: {r.mitre_attack.join(", ")}
                  </div>
                )}
                <p className="mt-2 text-xs text-slate-500">
                  <span className="font-semibold text-slate-400">Response:</span>{" "}
                  {r.recommended_action}
                </p>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
