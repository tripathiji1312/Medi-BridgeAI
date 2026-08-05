import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useDismissAlert } from "../src/hooks/useDismissAlert";

describe("useDismissAlert", () => {
  it("posts the reason and source utterance id to the session's dismissed-alerts endpoint", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve({}) });

    const { result } = renderHook(() => useDismissAlert("s1", { fetchImpl, gatewayHttpUrl: "http://gw" }));

    let succeeded = false;
    await act(async () => {
      succeeded = await result.current.dismiss("false positive", "u1");
    });

    expect(succeeded).toBe(true);
    expect(fetchImpl).toHaveBeenCalledWith(
      "http://gw/sessions/s1/dismissed-alerts",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ reason: "false positive", source_utterance_id: "u1" }),
      }),
    );
    expect(result.current.error).toBeNull();
  });

  it("returns false and sets an error without a session id, rather than silently no-opping", async () => {
    const fetchImpl = vi.fn();
    const { result } = renderHook(() => useDismissAlert(null, { fetchImpl, gatewayHttpUrl: "http://gw" }));

    let succeeded = true;
    await act(async () => {
      succeeded = await result.current.dismiss("reason", null);
    });

    expect(succeeded).toBe(false);
    expect(fetchImpl).not.toHaveBeenCalled();
    await waitFor(() => expect(result.current.error).not.toBeNull());
  });

  it("surfaces an error and returns false when the endpoint responds with a failure status", async () => {
    const fetchImpl = vi.fn().mockResolvedValue({ ok: false, status: 503 });
    const { result } = renderHook(() => useDismissAlert("s1", { fetchImpl, gatewayHttpUrl: "http://gw" }));

    let succeeded = true;
    await act(async () => {
      succeeded = await result.current.dismiss("reason", "u1");
    });

    expect(succeeded).toBe(false);
    expect(result.current.error).toContain("503");
  });

  it("surfaces an error and returns false when the fetch throws", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("network down"));
    const { result } = renderHook(() => useDismissAlert("s1", { fetchImpl, gatewayHttpUrl: "http://gw" }));

    let succeeded = true;
    await act(async () => {
      succeeded = await result.current.dismiss("reason", "u1");
    });

    expect(succeeded).toBe(false);
    expect(result.current.error).toBe("network down");
  });
});
