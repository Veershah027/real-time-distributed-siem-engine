import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api } from "@/services/api";
import { Card, Loading, ErrorState } from "@/components/primitives";

export function System() {
  const query = useQuery({
    queryKey: ["system-status"],
    queryFn: api.systemStatus,
    refetchInterval: 5000,
  });

  if (query.isLoading) return <Loading />;
  if (query.isError) return <ErrorState error={query.error} />;
  const s = query.data!;

  return (
    <div className="space-y-4">
      <Card title="Overview">
        <div className="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <Kv label="Status" value={s.status} tone={s.status === "healthy" ? "good" : "bad"} />
          <Kv label="Version" value={s.version} />
          <Kv label="Environment" value={s.env} />
          <Kv label="Uptime" value={`${Math.floor(s.uptime_seconds / 60)}m`} />
        </div>
      </Card>

      <Card title="Components">
        <div className="divide-y divide-base-750">
          {Object.entries(s.components).map(([name, info]) => (
            <div key={name} className="flex items-center justify-between px-4 py-3">
              <div>
                <div className="text-sm font-medium text-slate-200">{name}</div>
                <div className="text-xs text-slate-500">
                  {Object.entries(info)
                    .filter(([k]) => k !== "status")
                    .map(([k, v]) => `${k}: ${v}`)
                    .join("  ·  ") || "—"}
                </div>
              </div>
              <span
                className={clsx(
                  "rounded px-2 py-0.5 text-xs font-semibold",
                  info.status === "up"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : info.status === "idle" || info.status === "unknown"
                      ? "bg-slate-500/15 text-slate-400"
                      : "bg-sev-critical/15 text-sev-critical",
                )}
              >
                {String(info.status)}
              </span>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Message broker">
          <dl className="divide-y divide-base-750 text-sm">
            {Object.entries(s.broker).map(([k, v]) => (
              <div key={k} className="flex justify-between px-4 py-2">
                <dt className="text-slate-500">{k}</dt>
                <dd className="font-mono text-xs text-slate-300">{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
        <Card title="Feature flags">
          <dl className="divide-y divide-base-750 text-sm">
            {Object.entries(s.feature_flags).map(([k, v]) => (
              <div key={k} className="flex justify-between px-4 py-2">
                <dt className="text-slate-500">{k}</dt>
                <dd className="font-mono text-xs text-slate-300">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>
    </div>
  );
}

function Kv({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "good" | "bad";
}) {
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div
        className={clsx(
          "text-lg font-bold",
          tone === "good" && "text-emerald-400",
          tone === "bad" && "text-sev-high",
          !tone && "text-slate-100",
        )}
      >
        {value}
      </div>
    </div>
  );
}
