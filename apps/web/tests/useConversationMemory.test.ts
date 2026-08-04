import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useConversationMemory } from "../src/hooks/useConversationMemory";

const SAMPLE_MEMORY = {
  session_id: "s1",
  utterances: [{ id: "u1", speaker: "speaker_a", original_text: "hi", translated_text: "hi", sequence: 0 }],
  case_memory: [{ id: "c1", category: "symptom", value: "fever", source_utterance_id: "u1" }],
};

describe("useConversationMemory", () => {
  it("does not fetch when there is no session id", () => {
    const fetchImpl = vi.fn();
    renderHook(() => useConversationMemory(null, 0, { fetchImpl, gatewayHttpUrl: "http://gw" }));
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("fetches memory for the given session id", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(SAMPLE_MEMORY) });

    const { result } = renderHook(() =>
      useConversationMemory("s1", 0, { fetchImpl, gatewayHttpUrl: "http://gw" }),
    );

    await waitFor(() => expect(result.current.memory).not.toBeNull());
    expect(fetchImpl).toHaveBeenCalledWith("http://gw/sessions/s1/memory");
    expect(result.current.memory?.case_memory).toHaveLength(1);
    expect(result.current.error).toBeNull();
  });

  it("re-fetches when refreshTrigger changes", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(SAMPLE_MEMORY) });

    const { rerender } = renderHook(
      ({ trigger }) => useConversationMemory("s1", trigger, { fetchImpl, gatewayHttpUrl: "http://gw" }),
      { initialProps: { trigger: 0 } },
    );
    await waitFor(() => expect(fetchImpl).toHaveBeenCalledTimes(1));

    rerender({ trigger: 1 });
    await waitFor(() => expect(fetchImpl).toHaveBeenCalledTimes(2));
  });

  it("surfaces a visible error rather than silently showing an empty panel when the fetch fails", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: false, status: 503 });

    const { result } = renderHook(() =>
      useConversationMemory("s1", 0, { fetchImpl, gatewayHttpUrl: "http://gw" }),
    );

    await waitFor(() => expect(result.current.error).not.toBeNull());
    expect(result.current.error).toContain("503");
  });

  it("removeCaseMemoryEntry calls DELETE then re-fetches", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(SAMPLE_MEMORY) });

    const { result } = renderHook(() =>
      useConversationMemory("s1", 0, { fetchImpl, gatewayHttpUrl: "http://gw" }),
    );
    await waitFor(() => expect(result.current.memory).not.toBeNull());
    fetchImpl.mockClear();

    await act(async () => {
      await result.current.removeCaseMemoryEntry("c1");
    });

    expect(fetchImpl).toHaveBeenCalledWith("http://gw/sessions/s1/case-memory/c1", { method: "DELETE" });
    expect(fetchImpl).toHaveBeenCalledWith("http://gw/sessions/s1/memory"); // re-fetched after delete
  });
});
