import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskBadge } from "../src/components/shared/RiskBadge";
import { ThemeProvider } from "../src/theme/ThemeProvider";

describe("RiskBadge", () => {
  it("renders the level and reason, never a bare label", () => {
    render(
      <ThemeProvider>
        <RiskBadge level="medium" reason="2 symptom(s) mentioned (fever, cough)." />
      </ThemeProvider>,
    );

    expect(screen.getByText("Medium risk")).toBeInTheDocument();
    expect(screen.getByText(/fever, cough/)).toBeInTheDocument();
  });

  it("renders each level with its own label", () => {
    const { rerender } = render(
      <ThemeProvider>
        <RiskBadge level="low" reason="No symptoms detected." />
      </ThemeProvider>,
    );
    expect(screen.getByText("Low risk")).toBeInTheDocument();

    rerender(
      <ThemeProvider>
        <RiskBadge level="high" reason="Detected emergency keyword(s): chest pain." />
      </ThemeProvider>,
    );
    expect(screen.getByText("High risk")).toBeInTheDocument();
  });
});
