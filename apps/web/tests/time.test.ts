import { describe, expect, it } from "vitest";
import { formatMsAsTimestamp } from "../src/utils/time";

describe("formatMsAsTimestamp", () => {
  it("formats sub-minute durations", () => {
    expect(formatMsAsTimestamp(0)).toBe("0:00");
    expect(formatMsAsTimestamp(45_000)).toBe("0:45");
  });

  it("formats durations over a minute with zero-padded seconds", () => {
    expect(formatMsAsTimestamp(65_000)).toBe("1:05");
    expect(formatMsAsTimestamp(3_661_000)).toBe("61:01");
  });

  it("never returns a negative timestamp for negative input", () => {
    expect(formatMsAsTimestamp(-500)).toBe("0:00");
  });
});
