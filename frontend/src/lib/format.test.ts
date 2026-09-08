import { describe, expect, it } from "vitest";
import { humanBytes, compactNum, pct } from "./format";

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
  });
});
