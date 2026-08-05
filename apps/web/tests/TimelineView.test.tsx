import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TimelineView } from "../src/components/panels/TimelineView";
import { ThemeProvider } from "../src/theme/ThemeProvider";
import type { TimelineEvent } from "../src/hooks/useConversationMemory";

const EVENTS: TimelineEvent[] = [
  {
    id: "e1",
    type: "symptom_mentioned",
    description: "fever mentioned",
    source_utterance_id: "u1",
    timestamp: "2026-08-05T10:00:00.000Z",
  },
  {
    id: "e2",
    type: "risk_level_changed",
    description: "Risk level changed to medium",
    source_utterance_id: "u2",
    timestamp: "2026-08-05T10:01:00.000Z",
  },
];

describe("TimelineView", () => {
  it("shows a not-tracking message when there is no session", () => {
    render(
      <ThemeProvider>
        <TimelineView sessionId={null} events={[]} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/not tracking/i)).toBeInTheDocument();
  });

  it("shows a placeholder when there are no events yet", () => {
    render(
      <ThemeProvider>
        <TimelineView sessionId="s1" events={[]} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/no timeline events yet/i)).toBeInTheDocument();
  });

  it("renders each event's description in order", () => {
    render(
      <ThemeProvider>
        <TimelineView sessionId="s1" events={EVENTS} />
      </ThemeProvider>,
    );

    expect(screen.getByText("fever mentioned")).toBeInTheDocument();
    expect(screen.getByText("Risk level changed to medium")).toBeInTheDocument();
  });

  it("triggers a JSON download when Export is clicked", () => {
    const createObjectURL = vi.fn().mockReturnValue("blob:mock");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    render(
      <ThemeProvider>
        <TimelineView sessionId="s1" events={EVENTS} />
      </ThemeProvider>,
    );

    screen.getByRole("button", { name: /export/i }).click();

    expect(createObjectURL).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");

    clickSpy.mockRestore();
    vi.unstubAllGlobals();
  });

  it("disables Export when there are no events", () => {
    render(
      <ThemeProvider>
        <TimelineView sessionId="s1" events={[]} />
      </ThemeProvider>,
    );

    expect(screen.getByRole("button", { name: /export/i })).toBeDisabled();
  });
});
