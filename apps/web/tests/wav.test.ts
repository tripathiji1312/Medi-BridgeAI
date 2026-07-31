import { describe, expect, it } from "vitest";
import { pcm16ToWavDataUrl } from "../src/audio/wav";

describe("pcm16ToWavDataUrl", () => {
  it("produces a data URL with a valid 44-byte WAV header wrapping the original PCM bytes", () => {
    const pcmBytes = new Uint8Array([1, 2, 3, 4, 5, 6]);
    const base64Pcm = btoa(String.fromCharCode(...pcmBytes));

    const dataUrl = pcm16ToWavDataUrl(base64Pcm, 16_000);

    expect(dataUrl.startsWith("data:audio/wav;base64,")).toBe(true);

    const decoded = atob(dataUrl.replace("data:audio/wav;base64,", ""));
    const bytes = Uint8Array.from(decoded, (c) => c.charCodeAt(0));

    expect(bytes.length).toBe(44 + pcmBytes.length);
    expect(String.fromCharCode(...bytes.slice(0, 4))).toBe("RIFF");
    expect(String.fromCharCode(...bytes.slice(8, 12))).toBe("WAVE");
    expect(String.fromCharCode(...bytes.slice(36, 40))).toBe("data");

    // Sample rate is a little-endian uint32 at offset 24.
    const view = new DataView(bytes.buffer);
    expect(view.getUint32(24, true)).toBe(16_000);

    // Trailing bytes are the original PCM payload, unmodified.
    expect(Array.from(bytes.slice(44))).toEqual(Array.from(pcmBytes));
  });
});
