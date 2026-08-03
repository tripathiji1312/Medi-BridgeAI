import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WaveformMeter } from "../src/components/shared/WaveformMeter";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("WaveformMeter", () => {
  it("renders an accessible level indicator labeled for its speaker", () => {
    render(
      <ThemeProvider>
        <WaveformMeter level={0.5} label="Microphone" active />
      </ThemeProvider>,
    );

    expect(screen.getByRole("img", { name: "Microphone audio level" })).toBeInTheDocument();
  });

  it("does not throw for out-of-range levels, clamping instead", () => {
    expect(() =>
      render(
        <ThemeProvider>
          <WaveformMeter level={5} label="Microphone" active />
        </ThemeProvider>,
      ),
    ).not.toThrow();
  });
});
