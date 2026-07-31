import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useAudioCapture, type AudioContextLike, type ScriptProcessorNodeLike } from "../src/hooks/useAudioCapture";

function makeFakeMediaStream(): MediaStream {
  const track = { stop: vi.fn() };
  return { getTracks: () => [track] } as unknown as MediaStream;
}

function makeFakeAudioContext(sampleRate: number): {
  context: AudioContextLike;
  processor: ScriptProcessorNodeLike;
} {
  const processor: ScriptProcessorNodeLike = {
    onaudioprocess: null,
    connect: vi.fn(),
    disconnect: vi.fn(),
  };
  const context: AudioContextLike = {
    sampleRate,
    createMediaStreamSource: () => ({ connect: vi.fn() }),
    createScriptProcessor: () => processor,
    destination: {},
    close: vi.fn().mockResolvedValue(undefined),
  };
  return { context, processor };
}

describe("useAudioCapture", () => {
  it("starts recording and delivers PCM16 chunks derived from mic input", async () => {
    const onChunk = vi.fn();
    const getUserMedia = vi.fn().mockResolvedValue(makeFakeMediaStream());
    const { context, processor } = makeFakeAudioContext(16_000);
    const createAudioContext = vi.fn().mockReturnValue(context);

    const { result } = renderHook(() =>
      useAudioCapture({ onChunk, getUserMedia, createAudioContext }),
    );

    await act(async () => {
      await result.current.start();
    });

    await waitFor(() => expect(result.current.isRecording).toBe(true));
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(result.current.error).toBeNull();

    const samples = new Float32Array([0.5, -0.5, 0, 1]);
    act(() => {
      processor.onaudioprocess?.({ inputBuffer: { getChannelData: () => samples } });
    });

    expect(onChunk).toHaveBeenCalledTimes(1);
    const chunk = onChunk.mock.calls[0]?.[0] as ArrayBuffer;
    expect(chunk.byteLength).toBe(samples.length * 2); // 16kHz in == 16kHz out, no downsampling
  });

  it("surfaces a reason string when mic permission is denied, rather than failing silently", async () => {
    const onChunk = vi.fn();
    const getUserMedia = vi.fn().mockRejectedValue(new Error("Permission denied"));

    const { result } = renderHook(() => useAudioCapture({ onChunk, getUserMedia }));

    await act(async () => {
      await result.current.start();
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.error).toBe("Permission denied");
    expect(onChunk).not.toHaveBeenCalled();
  });

  it("stop() releases the mic track and audio context", async () => {
    const onChunk = vi.fn();
    const stream = makeFakeMediaStream();
    const getUserMedia = vi.fn().mockResolvedValue(stream);
    const { context, processor } = makeFakeAudioContext(16_000);
    const createAudioContext = vi.fn().mockReturnValue(context);

    const { result } = renderHook(() =>
      useAudioCapture({ onChunk, getUserMedia, createAudioContext }),
    );

    await act(async () => {
      await result.current.start();
    });

    act(() => {
      result.current.stop();
    });

    expect(processor.disconnect).toHaveBeenCalled();
    expect(context.close).toHaveBeenCalled();
    expect((stream.getTracks()[0] as { stop: () => void }).stop).toHaveBeenCalled();
    await waitFor(() => expect(result.current.isRecording).toBe(false));
  });
});
