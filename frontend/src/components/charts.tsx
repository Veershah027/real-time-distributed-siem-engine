import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { clockTime } from "@/lib/format";
import { EmptyState } from "./primitives";

const AXIS = { stroke: "#475569", fontSize: 11 };
const GRID = "#1e293b";
const TOOLTIP = {
  contentStyle: {
    background: "#0d1220",
    border: "1px solid #334155",
    borderRadius: 8,
    fontSize: 12,
  },
  labelStyle: { color: "#94a3b8" },
};

export const SEV_COLORS: Record<string, string> = {
  critical: "#f43f5e",
  high: "#fb923c",
  medium: "#facc15",
  low: "#38bdf8",
  info: "#64748b",
};

export function EventsAreaChart({ data }: { data: { bucket: string; count: number }[] }) {
  if (!data.length) return <EmptyState title="No event history yet" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -12 }}>
        <defs>
          <linearGradient id="ev" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="bucket" tickFormatter={clockTime} {...AXIS} minTickGap={40} />
        <YAxis {...AXIS} width={44} allowDecimals={false} />
        <Tooltip {...TOOLTIP} labelFormatter={clockTime} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#38bdf8"
          strokeWidth={2}
          fill="url(#ev)"
          name="events"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function AlertsBarChart({
  data,
}: {
  data: { bucket: string; [k: string]: string | number }[];
}) {
  if (!data.length) return <EmptyState title="No alerts in this window" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -12 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="bucket" tickFormatter={clockTime} {...AXIS} minTickGap={40} />
        <YAxis {...AXIS} width={44} allowDecimals={false} />
        <Tooltip {...TOOLTIP} labelFormatter={clockTime} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {["critical", "high", "medium", "low", "info"].map((s) => (
          <Bar key={s} dataKey={s} stackId="a" fill={SEV_COLORS[s]} name={s} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DistributionPie({
  data,
}: {
  data: { name: string; value: number; color?: string }[];
}) {
  if (!data.length || data.every((d) => d.value === 0))
    return <EmptyState title="Nothing to chart yet" />;
  const palette = ["#38bdf8", "#fb923c", "#a78bfa", "#34d399", "#facc15", "#f43f5e", "#64748b"];
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius="52%"
          outerRadius="80%"
          paddingAngle={2}
        >
          {data.map((d, i) => (
            <Cell key={d.name} fill={d.color ?? palette[i % palette.length]} />
          ))}
        </Pie>
        <Tooltip {...TOOLTIP} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function HBarChart({
  data,
  color = "#38bdf8",
}: {
  data: { name: string; value: number }[];
  color?: string;
}) {
  if (!data.length) return <EmptyState title="No data yet" />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
      >
        <CartesianGrid stroke={GRID} horizontal={false} />
        <XAxis type="number" {...AXIS} allowDecimals={false} />
        <YAxis type="category" dataKey="name" {...AXIS} width={120} />
        <Tooltip {...TOOLTIP} />
        <Bar dataKey="value" fill={color} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
