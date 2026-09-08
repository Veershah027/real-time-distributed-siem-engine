import { describe, expect, it } from "vitest";
import { compactNum, humanBytes, metric, ms, pct, signedPct } from "./format";

describe("format helpers", () => {
  it("humanBytes", () => {
    expect(humanBytes(0)).toBe("0 B");
    expect(humanBytes(1024)).toBe("1.0 KiB");
    expect(humanBytes(52_428_800)).toBe("50.0 MiB");
  });

  it("compactNum", () => {
    expect(compactNum(1500)).toMatch(/1.5K/i);
  });

  it("pct", () => {
    expect(pct(0.965)).toBe("96.5%");
    expect(pct(0.5, 0)).toBe("50%");
  });

  it("metric returns dash for null/undefined", () => {
    expect(metric(null)).toBe("—");
    expect(metric(undefined)).toBe("—");
    expect(metric(42.7, { digits: 0 })).toBe("43");
    expect(metric(3.14159, { suffix: " ms", digits: 2 })).toBe("3.14 ms");
  });

  it("ms formats latency", () => {
    expect(ms(null)).toBe("—");
    expect(ms(2.781)).toBe("2.78 ms");
    expect(ms(42)).toBe("42 ms");
  });

  it("signedPct", () => {
    expect(signedPct(null)).toBe("—");
    expect(signedPct(568)).toBe("+568%");
    expect(signedPct(-12)).toBe("-12%");
  });
});
