import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmotionIndicator } from "../src/components/shared/EmotionIndicator";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("EmotionIndicator", () => {
  it("renders the label and confidence percentage", () => {
    render(
      <ThemeProvider>
        <EmotionIndicator
          label="anxious"
          confidence={0.72}
          reason="Highly variable pitch with little pausing."
          disclaimer="Estimated from voice tone, not verified."
        />
      </ThemeProvider>,
    );

    expect(screen.getByText(/Tone: Anxious \(72%\)/)).toBeInTheDocument();
  });

  it("carries the reason and disclaimer in its tooltip, never silently omitted", () => {
    render(
      <ThemeProvider>
        <EmotionIndicator
          label="fearful"
          confidence={0.6}
          reason="Pitch well above typical with low volume."
          disclaimer="Estimated from voice tone, not verified."
        />
      </ThemeProvider>,
    );

    const chip = screen.getByText(/Tone: Fearful/);
    expect(chip.getAttribute("title")).toMatch(/Pitch well above typical/);
    expect(chip.getAttribute("title")).toMatch(/Estimated from voice tone, not verified/);
  });
});
