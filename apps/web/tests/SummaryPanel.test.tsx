import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SummaryPanel } from "../src/components/panels/SummaryPanel";
import { ThemeProvider } from "../src/theme/ThemeProvider";
import type { StructuredSummary } from "../src/hooks/useConversationMemory";

const SUMMARY: StructuredSummary = {
  patient_info: null,
  complaints: [{ text: "Fever for three days", source_utterance_id: "u1" }],
  symptoms: [{ text: "Fever", source_utterance_id: "u1" }],
  objective: [],
  diagnoses_mentioned: [],
  medications: [{ text: "Paracetamol twice a day", source_utterance_id: "u2" }],
  recommendations: [],
  action_items: [],
  follow_up: [],
  discarded_ungrounded_count: 0,
  model_name: "anthropic/claude-sonnet-4.5",
};

describe("SummaryPanel", () => {
  it("shows a not-tracking message when there is no session", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId={null}
          summary={null}
          approved={false}
          error={null}
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );
    expect(screen.getByText(/not tracking/i)).toBeInTheDocument();
  });

  it("calls onGenerate when the generate button is clicked", () => {
    const onGenerate = vi.fn();
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={null}
          approved={false}
          error={null}
          isGenerating={false}
          onGenerate={onGenerate}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /generate summary/i }));

    expect(onGenerate).toHaveBeenCalled();
  });

  it("renders a DRAFT label, grounded bullets by section, and never auto-approves", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={SUMMARY}
          approved={false}
          error={null}
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText(/DRAFT — AI-generated, not yet reviewed/)).toBeInTheDocument();
    expect(screen.getByText("Fever for three days")).toBeInTheDocument();
    expect(screen.getByText("Paracetamol twice a day")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /approve summary/i })).toBeInTheDocument();
  });

  it("shows APPROVED and hides the approve button once approved", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={SUMMARY}
          approved={true}
          error={null}
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText("APPROVED")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /approve summary/i })).not.toBeInTheDocument();
  });

  it("calls onApprove when the approve button is clicked", () => {
    const onApprove = vi.fn();
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={SUMMARY}
          approved={false}
          error={null}
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={onApprove}
        />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /approve summary/i }));

    expect(onApprove).toHaveBeenCalled();
  });

  it("shows the discarded-ungrounded-count transparently, not hidden", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={{ ...SUMMARY, discarded_ungrounded_count: 2 }}
          approved={false}
          error={null}
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByText(/2 proposed items could not be grounded/)).toBeInTheDocument();
  });

  it("surfaces a generation error rather than a silent empty panel", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={null}
          approved={false}
          error="clinical-nlp unavailable"
          isGenerating={false}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("clinical-nlp unavailable");
  });

  it("disables the generate button while generating", () => {
    render(
      <ThemeProvider>
        <SummaryPanel
          sessionId="s1"
          summary={null}
          approved={false}
          error={null}
          isGenerating={true}
          onGenerate={vi.fn()}
          onApprove={vi.fn()}
        />
      </ThemeProvider>,
    );

    expect(screen.getByRole("button", { name: /generating/i })).toBeDisabled();
  });
});
