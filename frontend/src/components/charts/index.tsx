import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { clockTime } from "@/lib/format";
import { SEVERITY_META, SEVERITY_ORDER, severityColor } from "@/lib/severity";
import { EmptyState } from "@/components/ui/primitives";

const AXIS = { stroke: "var(--text-faint)", fontSize: 10, tickLine: false, axisLine: false };
const GRID = "var(--grid-line)";
const TT = {
  contentStyle: {
    background: "var(--bg-elev)",
    border: "1px solid var(--border-strong)",
    borderRadius: 7,
    fontSize: 11,
    padding: "6px 9px",
  },
  labelStyle: { color: "var(--text-dim)", marginBottom: 2 },
  itemStyle: { padding: 0 },
};

const PALETTE = ["#3d7dff", "#8b5cf6", "#22d3ee", "#34d399", "#f5b445", "#fb7185", "#94a3b8"];

export function TimeSeriesArea({
  data,
  color = "var(--accent)",
  dataKey = "count",
  fmtX = clockTime,
}: {
  data: Record<string, unknown>[];
  color?: string;
  dataKey?: string;
  fmtX?: (v: string) => string;
}) {
  if (!data.length) return <EmptyState title="No history in window" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 6, right: 10, bottom: 0, left: -18 }}>
        <defs>
          <linearGradient id={`g-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="bucket" tickFormatter={fmtX} {...AXIS} minTickGap={44} />
        <YAxis {...AXIS} width={42} allowDecimals={false} />
        <Tooltip {...TT} labelFormatter={fmtX} />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={1.6}
          fill={`url(#g-${dataKey})`}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SeverityStackedBar({
  data,
}: {
  data: { bucket: string; [sev: string]: string | number }[];
}) {
  if (!data.length) return <EmptyState title="No alerts in window" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 6, right: 10, bottom: 0, left: -18 }} barCategoryGap={2}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="bucket" tickFormatter={clockTime} {...AXIS} minTickGap={44} />
        <YAxis {...AXIS} width={42} allowDecimals={false} />
        <Tooltip {...TT} labelFormatter={clockTime} />
        {SEVERITY_ORDER.map((s) => (
          <Bar key={s} dataKey={s} stackId="s" fill={SEVERITY_META[s].color} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MultiLine({
  data,
  series,
  fmtX = clockTime,
}: {
  data: Record<string, unknown>[];
  series: { key: string; label: string; color: string }[];
  fmtX?: (v: string) => string;
}) {
  if (!data.length) return <EmptyState title="No samples yet" hint="Data appears within a minute." />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 6, right: 12, bottom: 0, left: -14 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="t" tickFormatter={fmtX} {...AXIS} minTickGap={44} />
        <YAxis {...AXIS} width={44} />
        <Tooltip {...TT} labelFormatter={fmtX} />
        <Legend wrapperStyle={{ fontSize: 10, paddingTop: 4 }} iconType="plainline" />
        {series.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function Donut({ data }: { data: { name: string; value: number; color?: string }[] }) {
  const nonZero = data.filter((d) => d.value > 0);
  if (!nonZero.length) return <EmptyState title="Nothing to chart" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={nonZero}
          dataKey="value"
          nameKey="name"
          innerRadius="56%"
          outerRadius="82%"
          paddingAngle={2}
          isAnimationActive={false}
        >
          {nonZero.map((d, i) => (
            <Cell key={d.name} fill={d.color ?? PALETTE[i % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip {...TT} />
        <Legend wrapperStyle={{ fontSize: 10 }} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function HBar({
  data,
  color = "var(--accent)",
  onClick,
}: {
  data: { name: string; value: number; sub?: string }[];
  color?: string;
  onClick?: (name: string) => void;
}) {
  if (!data.length) return <EmptyState title="No data in window" />;
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="flex flex-col gap-1.5 p-3">
      {data.map((d) => (
        <button
          key={d.name}
          onClick={() => onClick?.(d.name)}
          disabled={!onClick}
          className="group grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 rounded px-1.5 py-1 text-left enabled:hover:bg-panel-2"
        >
          <div className="min-w-0">
            <div className="flex items-baseline justify-between gap-2">
              <span className="truncate font-mono text-[11.5px] text-dim group-enabled:group-hover:text-ink">
                {d.name}
              </span>
              {d.sub && <span className="shrink-0 text-2xs text-faint">{d.sub}</span>}
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-line">
              <div
                className="h-full rounded-full"
                style={{ width: `${(d.value / max) * 100}%`, background: color }}
              />
            </div>
          </div>
          <span className="tnum text-[12px] text-ink">{d.value.toLocaleString()}</span>
        </button>
      ))}
    </div>
  );
}

export function Sparkline({
  data,
  color = "var(--accent)",
  height = 32,
}: {
  data: number[];
  color?: string;
  height?: number;
}) {
  if (data.length < 2) return <div style={{ height }} />;
  const pts = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={pts} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={`sp-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.4}
          fill={`url(#sp-${color})`}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function Heatmap({
  buckets,
  severities,
  cells,
}: {
  buckets: string[];
  severities: string[];
  cells: { bucket: string; severity: string; count: number }[];
}) {
  const map = new Map<string, number>();
  let max = 1;
  for (const c of cells) {
    map.set(`${c.bucket}|${c.severity}`, c.count);
    max = Math.max(max, c.count);
  }
  return (
    <div className="overflow-x-auto p-3">
      <div className="inline-grid gap-1" style={{ gridTemplateColumns: `72px repeat(${buckets.length}, 1fr)` }}>
        <div />
        {buckets.map((b) => (
          <div key={b} className="text-center font-mono text-[9px] text-faint">
            {clockTime(b).slice(0, 5)}
          </div>
        ))}
        {severities.map((sev) => (
          <div key={sev} className="contents">
            <div className="flex items-center text-[10px] font-semibold" style={{ color: severityColor(sev) }}>
              {sev}
            </div>
            {buckets.map((b) => {
              const v = map.get(`${b}|${sev}`) ?? 0;
              return (
                <div
                  key={b + sev}
                  title={`${sev} · ${clockTime(b)} · ${v}`}
                  className="h-6 rounded-[3px] border border-line"
                  style={{
                    background: v ? severityColor(sev) : "var(--panel-2)",
                    opacity: v ? 0.25 + 0.75 * (v / max) : 1,
                  }}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
