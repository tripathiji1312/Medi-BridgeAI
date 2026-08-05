import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConversationMemoryPanel } from "../src/components/panels/ConversationMemoryPanel";
import { ThemeProvider } from "../src/theme/ThemeProvider";
import type { SessionMemory } from "../src/hooks/useConversationMemory";

const SAMPLE_MEMORY: SessionMemory = {
  session_id: "s1",
  utterances: [{ id: "u1", speaker: null, original_text: "x", translated_text: null, sequence: 0 }],
  case_memory: [{ id: "c1", category: "symptom", value: "fever", source_utterance_id: "u1" }],
  dismissed_alerts: [],
  timeline: [],
  draft_summary: null,
  summary_approved: false,
};

describe("ConversationMemoryPanel", () => {
  it("shows a not-tracking message when there is no session", () => {
    render(
      <ThemeProvider>
        <ConversationMemoryPanel sessionId={null} memory={null} error={null} removeCaseMemoryEntry={vi.fn()} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/not tracking/i)).toBeInTheDocument();
  });

  it("renders case memory chips from the given memory", () => {
    render(
      <ThemeProvider>
        <ConversationMemoryPanel
          sessionId="s1"
          memory={SAMPLE_MEMORY}
          error={null}
          removeCaseMemoryEntry={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText("fever")).toBeInTheDocument();
    expect(screen.getByText(/tracking 1 utterance/i)).toBeInTheDocument();
  });

  it("lets the clinician remove a case memory entry", () => {
    const removeCaseMemoryEntry = vi.fn();
    render(
      <ThemeProvider>
        <ConversationMemoryPanel
          sessionId="s1"
          memory={SAMPLE_MEMORY}
          error={null}
          removeCaseMemoryEntry={removeCaseMemoryEntry}
        />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByLabelText("Remove symptom fever from memory"));

    expect(removeCaseMemoryEntry).toHaveBeenCalledWith("c1");
  });

  it("surfaces a fetch error rather than silently showing an empty panel", () => {
    render(
      <ThemeProvider>
        <ConversationMemoryPanel
          sessionId="s1"
          memory={null}
          error="Conversation memory unavailable (status 503)"
          removeCaseMemoryEntry={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Conversation memory unavailable (status 503)");
  });
});
