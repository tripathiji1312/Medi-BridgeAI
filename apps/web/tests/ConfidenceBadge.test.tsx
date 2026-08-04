import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceBadge } from "../src/components/shared/ConfidenceBadge";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("ConfidenceBadge", () => {
  it("renders the score as a rounded percentage", () => {
    render(
      <ThemeProvider>
        <ConfidenceBadge score={0.873} band="green" />
      </ThemeProvider>,
    );
    expect(screen.getByText("Confidence: 87%")).toBeInTheDocument();
  });

  it("renders for each band without throwing", () => {
    for (const band of ["green", "yellow", "red"] as const) {
      expect(() =>
        render(
          <ThemeProvider>
            <ConfidenceBadge score={0.5} band={band} />
          </ThemeProvider>,
        ),
      ).not.toThrow();
    }
  });
});
