import { formatDistanceToNowStrict } from "date-fns";

export const relTime = (iso: string): string => {
  try {
    return formatDistanceToNowStrict(new Date(iso), { addSuffix: true });
  } catch {
    return iso;
  }
};

export const clockTime = (iso: string): string => {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return iso;
  }
};

export const fullTime = (iso: string): string => {
  try {
    return new Date(iso).toLocaleString([], { hour12: false });
  } catch {
    return iso;
  }
};

export const humanBytes = (n: number): string => {
  if (!n) return "0 B";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
  return `${(n / 1024 ** i).toFixed(1)} ${units[i]}`;
};

export const compactNum = (n: number): string =>
  Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const num = (n: number): string => Intl.NumberFormat().format(n);

export const pct = (n: number, digits = 1): string => `${(n * 100).toFixed(digits)}%`;

/** Format a possibly-null measured metric. `dash` when unavailable. */
export const metric = (
  v: number | null | undefined,
  opts: { suffix?: string; digits?: number; dash?: string } = {},
): string => {
  const { suffix = "", digits = 1, dash = "—" } = opts;
  if (v === null || v === undefined || Number.isNaN(v)) return dash;
  const rounded = Math.abs(v) >= 100 ? Math.round(v) : Number(v.toFixed(digits));
  return `${num(rounded)}${suffix}`;
};

export const ms = (v: number | null | undefined): string =>
  metric(v, { suffix: " ms", digits: v !== null && v !== undefined && v < 10 ? 2 : 0 });

export const signedPct = (v: number | null): string => {
  if (v === null || v === undefined) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(0)}%`;
};
