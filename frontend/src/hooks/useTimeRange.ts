import { useSyncExternalStore } from "react";

export interface TimeRange {
  label: string;
  minutes: number;
}

export const RANGES: TimeRange[] = [
  { label: "15m", minutes: 15 },
  { label: "1h", minutes: 60 },
  { label: "6h", minutes: 360 },
  { label: "24h", minutes: 1440 },
];

const KEY = "siem.timerange";
let current: TimeRange =
  RANGES.find((r) => String(r.minutes) === localStorage.getItem(KEY)) ?? RANGES[1];
const listeners = new Set<() => void>();

export function setTimeRange(r: TimeRange) {
  current = r;
  try {
    localStorage.setItem(KEY, String(r.minutes));
  } catch {
    /* storage blocked */
  }
  listeners.forEach((l) => l());
}

export function useTimeRange(): TimeRange {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => current,
  );
}

/** A sensible bucket size (seconds) for a given window. */
export function bucketFor(minutes: number): number {
  if (minutes <= 15) return 60;
  if (minutes <= 60) return 120;
  if (minutes <= 360) return 600;
  return 1800;
}
