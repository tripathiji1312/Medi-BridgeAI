import { describe, expect, it } from "vitest";
import { computeRmsLevel, downsampleBuffer, floatTo16BitPCM } from "../src/audio/pcm";

describe("downsampleBuffer", () => {
  it("returns the input unchanged when rates already match", () => {
    const input = new Float32Array([0.1, 0.2, 0.3]);
    expect(downsampleBuffer(input, 16_000, 16_000)).toBe(input);
  });

  it("halves the length when downsampling by a factor of 2", () => {
    const input = new Float32Array([1, 1, 0, 0, -1, -1, 0.5, 0.5]);
    const result = downsampleBuffer(input, 32_000, 16_000);
    expect(result).toHaveLength(4);
    expect(Array.from(result)).toEqual([1, 0, -1, 0.5]);
  });

  it("throws rather than silently upsampling", () => {
    const input = new Float32Array([0.1]);
    expect(() => downsampleBuffer(input, 16_000, 44_100)).toThrow();
  });
});

describe("floatTo16BitPCM", () => {
  it("encodes full-scale positive and negative samples correctly", () => {
    const input = new Float32Array([1, -1, 0]);
    const buffer = floatTo16BitPCM(input);
    const view = new DataView(buffer);

    expect(buffer.byteLength).toBe(6);
    expect(view.getInt16(0, true)).toBe(0x7fff);
    expect(view.getInt16(2, true)).toBe(-0x8000);
    expect(view.getInt16(4, true)).toBe(0);
  });

  it("clamps out-of-range samples rather than wrapping/corrupting them", () => {
    const input = new Float32Array([2.5, -3.0]);
    const view = new DataView(floatTo16BitPCM(input));

    expect(view.getInt16(0, true)).toBe(0x7fff);
    expect(view.getInt16(2, true)).toBe(-0x8000);
  });
});

describe("computeRmsLevel", () => {
  it("returns 0 for silence", () => {
    expect(computeRmsLevel(new Float32Array([0, 0, 0, 0]))).toBe(0);
  });

  it("returns 0 for an empty frame rather than dividing by zero", () => {
    expect(computeRmsLevel(new Float32Array([]))).toBe(0);
  });

  it("returns a higher level for louder audio", () => {
    const quiet = computeRmsLevel(new Float32Array([0.05, -0.05, 0.05, -0.05]));
    const loud = computeRmsLevel(new Float32Array([0.5, -0.5, 0.5, -0.5]));
    expect(loud).toBeGreaterThan(quiet);
  });

  it("always stays within [0, 1] even for full-scale input", () => {
    const level = computeRmsLevel(new Float32Array([1, -1, 1, -1]));
    expect(level).toBeGreaterThanOrEqual(0);
    expect(level).toBeLessThanOrEqual(1);
  });
});
