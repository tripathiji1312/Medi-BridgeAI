import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConversationMemoryPanel } from "../src/components/panels/ConversationMemoryPanel";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("ConversationMemoryPanel", () => {
  it("shows a not-tracking message when there is no session", () => {
    render(
      <ThemeProvider>
        <ConversationMemoryPanel sessionId={null} refreshTrigger={0} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/not tracking/i)).toBeInTheDocument();
  });

  it("renders case memory chips fetched for the active session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            session_id: "s1",
            utterances: [{ id: "u1", speaker: null, original_text: "x", translated_text: null, sequence: 0 }],
            case_memory: [{ id: "c1", category: "symptom", value: "fever", source_utterance_id: "u1" }],
          }),
      }),
    );

    render(
      <ThemeProvider>
        <ConversationMemoryPanel sessionId="s1" refreshTrigger={0} />
      </ThemeProvider>,
    );

    await waitFor(() => expect(screen.getByText("fever")).toBeInTheDocument());
    expect(screen.getByText(/tracking 1 utterance/i)).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("lets the clinician remove a case memory entry", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          session_id: "s1",
          utterances: [],
          case_memory: [{ id: "c1", category: "symptom", value: "fever", source_utterance_id: null }],
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <ThemeProvider>
        <ConversationMemoryPanel sessionId="s1" refreshTrigger={0} />
      </ThemeProvider>,
    );

    await waitFor(() => expect(screen.getByText("fever")).toBeInTheDocument());

    fireEvent.click(screen.getByLabelText("Remove symptom fever from memory"));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/sessions/s1/case-memory/c1"),
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    vi.unstubAllGlobals();
  });
});
