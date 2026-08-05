import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnalyticsDashboard } from "../src/components/panels/AnalyticsDashboard";
import { ThemeProvider } from "../src/theme/ThemeProvider";
import type { TranscriptEvent } from "@medibridge/shared-types";

function baseEvent(overrides: Partial<TranscriptEvent> = {}): TranscriptEvent {
  return {
    type: "final",
    utterance_id: "u1",
    session_id: "s1",
    segment: { text: "text", is_final: true, confidence: 0.9, start_ms: 0, end_ms: 1000, language: "hi" },
    error: null,
    latency_ms: null,
    translation: null,
    translation_error: null,
    tts: null,
    tts_error: null,
    speaker: null,
    speaker_error: null,
    back_translation: null,
    back_translation_error: null,
    miscommunication: null,
    miscommunication_error: null,
    confidence_v2: 0.85,
    confidence_band: "green",
    entities: null,
    entities_error: null,
    translation_entities: null,
    translation_entities_error: null,
    emergency: null,
    emergency_error: null,
    emotion: null,
    emotion_error: null,
    risk: null,
    risk_error: null,
    ...overrides,
  };
}

describe("AnalyticsDashboard", () => {
  it("shows a no-data placeholder when there are no finals yet", () => {
    render(
      <ThemeProvider>
        <AnalyticsDashboard finals={[]} />
      </ThemeProvider>,
    );
    expect(screen.getByText(/no data yet/i)).toBeInTheDocument();
  });

  it("renders consultation time, symptom count, and avg confidence tiles", () => {
    render(
      <ThemeProvider>
        <AnalyticsDashboard finals={[baseEvent()]} />
      </ThemeProvider>,
    );

    expect(screen.getByText("Consultation time")).toBeInTheDocument();
    expect(screen.getByText("Symptom count")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("shows the emotion trend tile only when emotion data is present", () => {
    const { rerender } = render(
      <ThemeProvider>
        <AnalyticsDashboard finals={[baseEvent()]} />
      </ThemeProvider>,
    );
    expect(screen.queryByText("Emotion trend")).not.toBeInTheDocument();

    rerender(
      <ThemeProvider>
        <AnalyticsDashboard
          finals={[baseEvent({ emotion: { label: "calm", confidence: 0.6, reason: "r", disclaimer: "d" } })]}
        />
      </ThemeProvider>,
    );
    expect(screen.getByText("Emotion trend")).toBeInTheDocument();
    expect(screen.getByText("calm: 1")).toBeInTheDocument();
  });
});
